"""synth-ai コマンドラインインターフェース。"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from synth_ai import __version__

if TYPE_CHECKING:
    from synth_ai.config import LocalConfig
from synth_ai.registry import ADAPTER_FACTORIES, get_adapter

app = typer.Typer(no_args_is_help=True, help="AI Sound Designer")
trial_app = typer.Typer(no_args_is_help=True, help="試行（録音と比較）の記録")
app.add_typer(trial_app, name="trial")


@app.command()
def version() -> None:
    """バージョンを表示する。"""
    typer.echo(__version__)


@app.command()
def adapters() -> None:
    """登録済みの機種と Capabilities を表示する。"""
    for synth_id in sorted(ADAPTER_FACTORIES):
        caps = get_adapter(synth_id).capabilities()
        typer.echo(caps.model_dump_json(indent=2))


@app.command()
def analyze(
    wav: Annotated[Path, typer.Argument(help="解析する参照WAV（単音）")],
    out: Annotated[Path, typer.Option("--out", "-o", help="出力先ディレクトリ")],
    analysis_id: Annotated[
        str | None, typer.Option("--id", help="解析ID（既定: ref-<sha256先頭8桁>）")
    ] = None,
    plots: Annotated[bool, typer.Option("--plots/--no-plots", help="グラフを出力する")] = True,
) -> None:
    """参照WAVを解析し、analysis.json とグラフを出力する。"""
    from synth_ai.core.audio.analyze import analyze_file
    from synth_ai.core.audio.load import AudioLoadError
    from synth_ai.core.audio.plots import plot_all
    from synth_ai.core.audio.summary import summarize
    from synth_ai.core.sound_spec.io import save_json

    try:
        result = analyze_file(wav, analysis_id)
    except AudioLoadError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    save_json(result.analysis, out / "analysis.json")
    written = [out / "analysis.json"]
    # 比較のときに同じ参照音を使えるよう、試行ディレクトリにコピーしておく
    reference_copy = out / "reference.wav"
    if wav.resolve() != reference_copy.resolve():
        shutil.copyfile(wav, reference_copy)
        written.append(reference_copy)
    if plots:
        written += plot_all(result, out)
    typer.echo(summarize(result.analysis))
    typer.echo("\n出力:")
    for path in written:
        typer.echo(f"  {path}")


@app.command()
def spec(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
) -> None:
    """analysis.json から機種非依存の sound_spec.json を作る。"""
    from synth_ai.core.workflow.files import MissingRunFileError, write_sound_spec

    try:
        sound_spec, path = write_sound_spec(run_dir)
    except MissingRunFileError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    t, e = sound_spec.timbre, sound_spec.envelope
    typer.echo(f"SoundSpec: {sound_spec.spec_id}")
    typer.echo(
        f"  音色: 倍音 {t.harmonicity} / 明るさ {t.brightness} / "
        f"明るさの減衰 {t.brightness_decay} / ノイズ {t.noisiness}"
    )
    typer.echo(f"  包絡: A {e.attack} / D {e.decay} / S {e.sustain} / R {e.release}")
    for h in sound_spec.hypotheses:
        typer.echo(f"  仮説: {h.method.value} ({h.confidence:.2f}) {h.rationale}")
    for u in sound_spec.uncertainties:
        typer.echo(f"  注意: {u}")
    typer.echo(f"\n出力: {path}")


@app.command()
def recipe(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    synth: Annotated[str, typer.Option("--synth", "-s", help="対象機種")] = "kronos2",
) -> None:
    """SoundSpec から機種別のレシピ（recipe.json / recipe.md）を作る。"""
    from synth_ai.core.workflow.files import MissingRunFileError, write_recipe
    from synth_ai.core.workflow.recipe import RecipeContractError

    try:
        files = write_recipe(run_dir, get_adapter(synth))
    except (MissingRunFileError, ValueError, RecipeContractError) as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(files.markdown_path.read_text(encoding="utf-8"))
    typer.echo(f"出力:\n  {files.json_path}\n  {files.markdown_path}")


@app.command()
def compare(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    recording: Annotated[Path, typer.Argument(help="シンセで鳴らして録音した WAV")],
    synth: Annotated[str | None, typer.Option("--synth", "-s", help="対象機種")] = "kronos2",
    plots: Annotated[bool, typer.Option("--plots/--no-plots", help="グラフを出力する")] = True,
) -> None:
    """録音を参照音と比べ、差分と次の調整案を試行として保存する。"""
    from synth_ai.core.audio.load import AudioLoadError
    from synth_ai.core.workflow.files import MissingRunFileError
    from synth_ai.core.workflow.trial import ReferenceMismatchError, run_trial

    try:
        adapter = get_adapter(synth) if synth else None
        result = run_trial(run_dir, recording, adapter, plots=plots)
    except (AudioLoadError, MissingRunFileError, ReferenceMismatchError, ValueError) as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(result.markdown)
    typer.echo(f"出力: {result.directory}")


@trial_app.command("list")
def trial_list(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
) -> None:
    """試行の一覧（距離、主な違い、評価）を表示する。"""
    from synth_ai.core.history.store import rebuild_history

    history = rebuild_history(run_dir)
    if not history.trials:
        typer.echo("試行はまだありません（synth-ai compare で追加）")
        return
    for t in history.trials:
        note = t.note
        rating = (
            f"近さ {note.closeness or '-'} / 好み {note.preference or '-'}" if note else "未評価"
        )
        typer.echo(
            f"[{t.trial:03d}] {t.created_at}  距離 {t.distance_db:.1f} dB  "
            f"有意な差 {t.significant_differences} 件  {rating}"
        )
        for d in t.top_differences:
            typer.echo(f"      - {d}")
        if note and note.memo:
            typer.echo(f"      メモ: {note.memo}")


@trial_app.command("note")
def trial_note(
    run_dir: Annotated[Path, typer.Argument(help="analyze の出力ディレクトリ")],
    trial: Annotated[int, typer.Argument(help="試行番号")],
    closeness: Annotated[
        int | None, typer.Option(min=1, max=5, help="目標への近さ（1〜5）")
    ] = None,
    preference: Annotated[int | None, typer.Option(min=1, max=5, help="好み（1〜5）")] = None,
    memo: Annotated[str | None, typer.Option(help="感想・気づき")] = None,
    change: Annotated[
        list[str] | None, typer.Option(help="実機で変えた内容（複数回指定可）")
    ] = None,
) -> None:
    """試行に人の評価を記録する。近さと好みは別々に記録する。"""
    from synth_ai.core.history.store import save_note

    try:
        note = save_note(
            run_dir,
            trial,
            closeness=closeness,
            preference=preference,
            memo=memo,
            changes=tuple(change or ()),
        )
    except FileNotFoundError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(note.model_dump_json(indent=2))


ConfigOption = Annotated[
    Path | None, typer.Option("--config", help="設定ファイル（既定: config/local.yaml）")
]


def _config(path: Path | None) -> LocalConfig:
    from synth_ai.config import ConfigError, load_config

    try:
        return load_config(path)
    except ConfigError as exc:
        typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


def _fail(exc: Exception) -> typer.Exit:
    typer.secho(f"エラー: {exc}", fg=typer.colors.RED, err=True)
    return typer.Exit(code=2)


@app.command()
def devices(config: ConfigOption = None) -> None:
    """接続中の MIDI 出力ポートと録音デバイスを表示する（* は設定で選ばれているもの）。"""
    from synth_ai.infrastructure.capture.recorder import input_devices
    from synth_ai.infrastructure.midi.sender import output_port_names

    cfg = _config(config)
    wanted_port = (cfg.midi.output_port or "").lower()
    wanted_input = (cfg.capture.input_device or "").lower()
    typer.echo("MIDI 出力ポート:")
    ports = output_port_names()
    for name in ports:
        mark = "*" if wanted_port and wanted_port in name.lower() else " "
        typer.echo(f"  {mark} {name}")
    if not ports:
        typer.echo("    （なし）KRONOS を USB で接続し、電源が入っているか確認してください")
    typer.echo("録音デバイス（入力）:")
    for d in input_devices():
        mark = "*" if wanted_input and wanted_input in d.name.lower() else " "
        typer.echo(f"  {mark} {d.name}（{d.channels} ch、既定 {d.default_sample_rate:.0f} Hz）")


@app.command("midi-probe")
def midi_probe(
    note: Annotated[str | None, typer.Option(help="音名（既定: 設定の test_note.note）")] = None,
    velocity: Annotated[int | None, typer.Option(min=1, max=127)] = None,
    hold: Annotated[float | None, typer.Option(help="押さえる秒数")] = None,
    port: Annotated[str | None, typer.Option(help="MIDI 出力ポート（既定: 設定）")] = None,
    channel: Annotated[int | None, typer.Option(min=1, max=16)] = None,
    config: ConfigOption = None,
) -> None:
    """MIDI で 1 音だけ鳴らし、PC から発音できるか確かめる（Note On/Off のみ送信）。"""
    from synth_ai.core.audio.notes import note_to_midi
    from synth_ai.infrastructure.midi.sender import MidiError, open_sender

    cfg = _config(config)
    port_name = port or cfg.midi.output_port
    if not port_name:
        raise _fail(ValueError("MIDI 出力ポートが未設定です（--port または config/local.yaml）"))
    note_name = note or cfg.test_note.note
    try:
        number = note_to_midi(note_name)
        with open_sender(port_name, channel or cfg.midi.channel) as sender:
            typer.echo(f"{port_name} に {note_name}（{number}）を送ります")
            sender.play(number, velocity or cfg.test_note.velocity, hold or cfg.test_note.hold_s)
    except (MidiError, ValueError) as exc:
        raise _fail(exc) from exc
    typer.echo("送信しました。KRONOS から音が出たか確認してください")


@app.command()
def capture(
    out: Annotated[Path | None, typer.Argument(help="保存先 WAV（--run 指定時は省略可）")] = None,
    run_dir: Annotated[
        Path | None,
        typer.Option("--run", help="参照音の run。音程を参照に合わせ、録音後に比較する"),
    ] = None,
    note: Annotated[
        str | None, typer.Option(help="音名（既定: 参照音の音程、なければ設定）")
    ] = None,
    velocity: Annotated[int | None, typer.Option(min=1, max=127)] = None,
    hold: Annotated[float | None, typer.Option(help="押さえる秒数")] = None,
    tail: Annotated[float | None, typer.Option(help="離した後に録音を続ける秒数")] = None,
    manual: Annotated[bool, typer.Option(help="MIDI を使わず手で弾く")] = False,
    compare_after: Annotated[
        bool, typer.Option("--compare/--no-compare", help="--run 指定時、録音後に比較する")
    ] = True,
    config: ConfigOption = None,
) -> None:
    """1 音を録音する。MIDI が設定されていれば PC から発音し、なければ合図に合わせて手で弾く。"""
    from contextlib import nullcontext
    from datetime import datetime

    from synth_ai.core.audio.notes import note_to_midi
    from synth_ai.core.sound_spec.io import load_json
    from synth_ai.core.sound_spec.models import AudioAnalysis
    from synth_ai.infrastructure.capture.recorder import (
        CaptureError,
        CaptureSettings,
        SoundDeviceRecorder,
        capture_note,
        write_capture,
    )
    from synth_ai.infrastructure.midi.sender import MidiError, open_sender

    cfg = _config(config)
    if out is None and run_dir is None:
        raise _fail(ValueError("保存先 WAV か --run を指定してください"))

    note_name = note
    if note_name is None and run_dir is not None:
        analysis_path = run_dir / "analysis.json"
        if analysis_path.is_file():
            pitch = load_json(AudioAnalysis, analysis_path).pitch
            if pitch is not None:
                note_name = pitch.note
                if pitch.confidence < 0.5:
                    typer.echo(f"注意: 参照音のピッチ確信度が低い（{pitch.confidence:.2f}）")
    note_name = note_name or cfg.test_note.note
    if out is None:
        assert run_dir is not None
        out = run_dir / "takes" / f"take-{datetime.now():%Y%m%d-%H%M%S}.wav"

    try:
        settings = CaptureSettings(
            note=note_to_midi(note_name),
            velocity=velocity or cfg.test_note.velocity,
            hold_s=hold or cfg.test_note.hold_s,
            release_tail_s=cfg.test_note.release_tail_s if tail is None else tail,
            pre_roll_s=cfg.capture.pre_roll_s,
            fade_ms=cfg.capture.fade_ms,
            peak_warn_dbfs=cfg.capture.peak_warn_dbfs,
            quiet_warn_dbfs=cfg.capture.quiet_warn_dbfs,
        )
        recorder = SoundDeviceRecorder(
            cfg.capture.input_device, cfg.capture.sample_rate, cfg.capture.channels
        )
        use_midi = not manual and cfg.midi.output_port is not None
        if not manual and not use_midi:
            typer.echo("MIDI 出力ポートが未設定のため、手で弾いて録音します")
        sender_ctx = (
            open_sender(cfg.midi.output_port, cfg.midi.channel)  # type: ignore[arg-type]
            if use_midi
            else nullcontext(None)
        )
        typer.echo(f"録音: {note_name}（ノート {settings.note}、ベロシティ {settings.velocity}）")
        with sender_ctx as sender:
            result = capture_note(recorder, sender, settings, prompt=typer.echo)
        write_capture(out, result)
    except (CaptureError, MidiError, ValueError) as exc:
        raise _fail(exc) from exc

    typer.echo(f"保存しました: {out}（ピーク {result.peak_dbfs:.1f} dBFS）")
    for w in result.warnings:
        typer.secho(f"注意: {w}", fg=typer.colors.YELLOW)
    if run_dir is not None and compare_after:
        typer.echo("")
        compare(run_dir, out, cfg.synth, plots=True)


@app.command("test-signals")
def test_signals(
    out: Annotated[Path, typer.Argument(help="出力先ディレクトリ")] = Path("assets/test"),
) -> None:
    """解析器の確認用に合成テスト音（WAV）を書き出す。"""
    from synth_ai.core.synthesis.test_signals import standard_set, write_wav

    for name, samples in standard_set().items():
        typer.echo(str(write_wav(out / f"{name}.wav", samples)))


if __name__ == "__main__":
    app()
