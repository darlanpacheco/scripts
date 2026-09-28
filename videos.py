#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

CRF_480 = 18
CRF_720 = 20
CRF_1080 = 24
AUDIO_BITRATE = "64k"


class MediaValidator:
    """Responsável por validar a existência de arquivos de mídia."""

    @staticmethod
    def validate_input(path: Path) -> None:
        if not path.exists():
            print(f"Erro: O arquivo de entrada '{path}' não existe.", file=sys.stderr)
            sys.exit(1)


class MediaInspector:
    """Responsável por inspecionar faixas de mídia usando ffprobe."""

    @staticmethod
    def get_video_height(file_path: Path) -> int:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=height",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            return 1080

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
    """Responsável por construir a lista de argumentos para o FFmpeg."""

    def __init__(self, input_path: Path, output_path: Path):
        self.input_path = input_path
        self.output_path = output_path
        self.cmd = [
            "ffmpeg",
            "-i",
            str(self.input_path),
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
        ]

    def add_video(self, track_idx: int, video_enc: str) -> "FfmpegCommandBuilder":
        height = MediaInspector.get_video_height(self.input_path)
        crf = CRF_1080
        if height == 480:
            crf = CRF_480
        elif height == 720:
            crf = CRF_720
        elif height == 1080:
            crf = CRF_1080

        self.cmd.extend(
            [
                "-map",
                f"0:v:{track_idx}?",
                "-c:v",
                video_enc,
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(crf),
            ]
        )
        return self

    def add_audio(self, track_idx: int, audio_enc: str) -> "FfmpegCommandBuilder":
        self.cmd.extend(
            [
                "-map",
                f"0:a:{track_idx}?",
                "-c:a",
                audio_enc,
                "-b:a",
                AUDIO_BITRATE,
            ]
        )
        return self

    def add_subtitle(self, track_idx: int, sub_enc: str) -> "FfmpegCommandBuilder":
        self.cmd.extend(["-map", f"0:s:{track_idx}?", "-c:s", sub_enc])
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

    def execute(self) -> None:
        MediaValidator.validate_input(self.input_path)

        if self.args.probe or self.args.raw:
            MediaInspector.probe(self.input_path, raw_json=self.args.raw)
            return

        if not self.output_path:
            print(
                "Erro: O argumento -o/--output é obrigatório para o processamento.",
                file=sys.stderr,
            )
            sys.exit(1)

        builder = FfmpegCommandBuilder(self.input_path, self.output_path)

        v_track = self.args.video_track
        v_enc = self.args.video_enc
        a_track = self.args.audio_track
        a_enc = self.args.audio_enc
        s_track = self.args.sub_track
        s_enc = self.args.sub_enc

        if v_track is None and a_track is None and s_track is None:
            builder.cmd.extend(["-map", "0", "-c", "copy"])
        else:
            if v_track is not None:
                actual_v_enc = v_enc if v_enc is not None else "libx265"
                builder.add_video(v_track, actual_v_enc)
            if a_track is not None:
                actual_a_enc = a_enc if a_enc is not None else "libopus"
                builder.add_audio(a_track, actual_a_enc)
            if s_track is not None:
                actual_s_enc = s_enc if s_enc is not None else "copy"
                builder.add_subtitle(s_track, actual_s_enc)

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
        description="Utilitário em Python para inspecionar e codificar mídia explicitamente."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Vídeo principal (obrigatório)",
    )
    parser.add_argument(
        "-p",
        "--probe",
        action="store_true",
        help="Inspeciona as faixas do arquivo de entrada formatadas",
    )
    parser.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Retorna a saída do probe em formato JSON bruto",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Arquivo MKV de saída final",
    )
    parser.add_argument(
        "-v",
        "--video-track",
        type=int,
        help="Índice da faixa de vídeo",
    )
    parser.add_argument(
        "-ve",
        "--video-enc",
        help="Codec de vídeo (padrão: libx265 se -v for informado)",
    )
    parser.add_argument(
        "-a",
        "--audio-track",
        type=int,
        help="Índice da faixa de áudio",
    )
    parser.add_argument(
        "-ae",
        "--audio-enc",
        help="Codec de áudio (padrão: libopus se -a for informado)",
    )
    parser.add_argument(
        "-s",
        "--sub-track",
        type=int,
        help="Índice da faixa de legenda",
    )
    parser.add_argument(
        "-se",
        "--sub-enc",
        help="Codec de legenda (padrão: copy se -s for informado)",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    processor = MediaProcessor(args)
    processor.execute()


if __name__ == "__main__":
    main()
