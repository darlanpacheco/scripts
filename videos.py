#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

CRF_480 = 22
CRF_720 = 26
CRF_1080 = 32
AUDIO_BITRATE = "128k"


class MediaValidator:
    """Responsável por validar a existência de arquivos de mídia (Single Responsibility Principle)."""

    @staticmethod
    def validate_input(path: Path) -> None:
        if not path.exists():
            print(f"Erro: O arquivo de entrada '{path}' não existe.", file=sys.stderr)
            sys.exit(1)

    @staticmethod
    def validate_donor(path: Path) -> None:
        if not path.exists():
            print(f"Erro: O arquivo doador '{path}' não existe.", file=sys.stderr)
            sys.exit(1)


class MediaInspector:
    """Responsável por inspecionar faixas de mídia usando ffprobe (Single Responsibility Principle)."""

    @staticmethod
    def probe(file_path: Path, raw_json: bool = False) -> None:
        MediaValidator.validate_input(file_path)

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,height,width:stream_tags=language,title",
            "-of",
            "json",
            str(file_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if raw_json:
                print(result.stdout)
                return
            data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao rodar ffprobe: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"\nArquivo: {file_path.name}\n" + "-" * 50)

        # Contadores separados por tipo para mostrar o índice relativo (ex: 0:v:0, 0:a:0)
        v_count = 0
        a_count = 0
        s_count = 0

        for stream in data.get("streams", []):
            st_type = stream.get("codec_type")
            idx = stream.get("index")
            codec = stream.get("codec_name", "desconhecido")

            if st_type == "video":
                rel_idx = v_count
                v_count += 1
                type_label = f"VÍDEO (mapeamento: -v {rel_idx})"
            elif st_type == "audio":
                rel_idx = a_count
                a_count += 1
                type_label = f"ÁUDIO (mapeamento: -a {rel_idx})"
            elif st_type == "subtitle":
                rel_idx = s_count
                s_count += 1
                type_label = f"LEGENDA (mapeamento: -s {rel_idx})"
            else:
                type_label = st_type.upper() if st_type else "OUTRO"

            info = f"[{idx}] {type_label} | Codec: {codec}"

            if st_type == "video":
                w = stream.get("width")
                h = stream.get("height")
                if w and h:
                    info += f" | Resolução: {w}x{h}"

            tags = stream.get("tags", {})
            lang = tags.get("language", "und")
            title = tags.get("title", "")

            info += f" | Idioma: {lang}"
            if title:
                info += f" | Título: {title}"

            print(info)
        print("-" * 50)


class FfmpegCommandBuilder:
    """Responsável exclusivamente por construir a lista de argumentos para o FFmpeg (Open/Closed Principle)."""

    def __init__(
        self, input_path: Path, output_path: Path, donor_path: Path | None = None
    ):
        self.input_path = input_path
        self.output_path = output_path
        self.donor_path = donor_path
        self.cmd = ["ffmpeg", "-i", str(self.input_path)]

        if self.donor_path:
            self.cmd.extend(["-i", str(self.donor_path)])

        self.cmd.extend(["-map_metadata", "-1", "-map_chapters", "-1"])

    def add_video(self, track_idx: int | None) -> "FfmpegCommandBuilder":
        if track_idx is not None:
            self.cmd.extend(["-map", f"0:v:{track_idx}", "-c:v", "copy"])
        return self

    def add_audio(self, track_idx: int | None) -> "FfmpegCommandBuilder":
        if track_idx is not None:
            source_idx = "1" if self.donor_path else "0"
            self.cmd.extend(
                [
                    "-map",
                    f"{source_idx}:a:{track_idx}",
                    "-c:a",
                    "libopus",
                    "-b:a",
                    AUDIO_BITRATE,
                ]
            )
        return self

    def add_subtitle(self, track_idx: int | None, codec: str) -> "FfmpegCommandBuilder":
        if track_idx is not None:
            self.cmd.extend(["-map", f"0:s:{track_idx}?", "-c:s", codec])
        return self

    def build(self) -> list[str]:
        self.cmd.append(str(self.output_path))
        return self.cmd


class MediaProcessor:
    """Orquestra a validação, construção do comando e execução do processo."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.input_path = Path(args.input)
        self.output_path = Path(args.output) if args.output else None
        self.donor_path = Path(args.donor) if args.donor else None

    def execute(self) -> None:
        MediaValidator.validate_input(self.input_path)
        if self.donor_path:
            MediaValidator.validate_donor(self.donor_path)

        if self.args.probe:
            MediaInspector.probe(self.input_path, raw_json=self.args.json)
            return

        if not self.output_path:
            print(
                "Erro: O argumento -o/--output é obrigatório para multiplexação.",
                file=sys.stderr,
            )
            sys.exit(1)

        builder = FfmpegCommandBuilder(
            self.input_path, self.output_path, self.donor_path
        )

        builder.add_video(self.args.video_track)
        builder.add_audio(self.args.audio_track)
        builder.add_subtitle(self.args.sub_track, self.args.sub_enc)

        cmd = builder.build()

        print(f"Executando: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True)
            print(f"\nSucesso! Arquivo salvo em: {self.output_path}")
        except subprocess.CalledProcessError as e:
            print(
                f"Erro crítico durante o processamento do FFmpeg: {e}", file=sys.stderr
            )
            sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Utilitário em Python para inspecionar, multiplexar e converter mídia estritamente por comandos."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Vídeo principal de alta qualidade (obrigatório)",
    )
    parser.add_argument(
        "-p",
        "--probe",
        action="store_true",
        help="Inspeciona as faixas do arquivo de entrada",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Retorna a saída do probe em formato JSON bruto",
    )
    parser.add_argument(
        "-d", "--donor", help="Vídeo doador contendo o áudio alternativo"
    )
    parser.add_argument("-o", "--output", help="Arquivo MKV de saída final")
    parser.add_argument(
        "-v",
        "--video-track",
        type=int,
        help="Índice da faixa de vídeo a ser copiada (ex: 0)",
    )
    parser.add_argument(
        "-a",
        "--audio-track",
        type=int,
        help="Índice da faixa de áudio a ser processada",
    )
    parser.add_argument(
        "-s", "--sub-track", type=int, help="Índice da faixa de legenda"
    )
    parser.add_argument(
        "-e", "--sub-enc", default="copy", help="Codec de legenda (padrão: copy)"
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    processor = MediaProcessor(args)
    processor.execute()


if __name__ == "__main__":
    main()
