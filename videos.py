#!/usr/bin/env python3

import argparse
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
        self.output_path = Path(args.output)
        self.donor_path = Path(args.donor) if args.donor else None

    def execute(self) -> None:
        MediaValidator.validate_input(self.input_path)
        if self.donor_path:
            MediaValidator.validate_donor(self.donor_path)

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
        description="Utilitário em Python para multiplexar e converter mídia estritamente por comandos."
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Vídeo principal de alta qualidade"
    )
    parser.add_argument(
        "-d", "--donor", help="Vídeo doador contendo o áudio alternativo"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Arquivo MKV de saída final"
    )
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
