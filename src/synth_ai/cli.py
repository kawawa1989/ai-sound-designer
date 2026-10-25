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


def _default_values(lo: float, hi: float, count: int = 8) -> tuple[float, ...]:
    """範囲を count 段に分けた整数値。両極性の範囲は 0 から上限まで。"""
    start = 0.0 if lo < 0 < hi else lo
    step = (hi - start) / (count - 1)
    return tuple(sorted({float(round(start + i * step)) for i in range(count)}))


@app.command()
def calibrate(
    parameter_id: Annotated[
        str | None, typer.Argument(help="パラメータ ID（省略すると測れるパラメータの一覧）")
    ] = None,
    values: Annotated[
        str | None, typer.Option(help="測る値（カンマ区切り。既定: 範囲を 8 段に分ける）")
    ] = None,
    feature: Annotated[
        str | None, typer.Option(help="測る特徴（既定: パラメータ表の役割から決まるもの）")
    ] = None,
    note: Annotated[str | None, typer.Option(help="音名（既定: 設定の test_note.note）")] = None,
    velocity: Annotated[int | None, typer.Option(min=1, max=127)] = None,
    hold: Annotated[float | None, typer.Option(help="押さえる秒数")] = None,
    tail: Annotated[float | None, typer.Option(help="離した後に録音を続ける秒数")] = None,
    conditions: Annotated[str, typer.Option(help="測定条件のメモ（基準の音色など）")] = "",
    manual: Annotated[bool, typer.Option(help="MIDI を使わず手で弾く")] = False,
    overwrite: Annotated[bool, typer.Option(help="既存の曲線を確認なしで上書きする")] = False,
    config: ConfigOption = None,
) -> None:
    """実機でパラメータを数段階変えて録音し、キャリブレーション曲線を作る（対話式）。"""
    from contextlib import nullcontext
    from datetime import datetime

    from synth_ai.adapters.base import ParameterCatalog
    from synth_ai.core.audio.analyze import analyze_file
    from synth_ai.core.audio.load import AudioLoadError
    from synth_ai.core.audio.notes import note_to_midi
    from synth_ai.core.calibration.session import (
        MIN_HOLD_S,
        MIN_TAIL_S,
        CalibrationPlan,
        Measurement,
        NotEnoughPointsError,
        Step,
        Verdict,
        build_curve,
        curve_filename,
        run_session,
    )
    from synth_ai.core.sound_spec.features import LABELS, UNITS, Feature
    from synth_ai.core.sound_spec.io import save_json
    from synth_ai.infrastructure.capture.recorder import (
        CaptureError,
        CaptureSettings,
        SoundDeviceRecorder,
        capture_note,
        write_capture,
    )
    from synth_ai.infrastructure.midi.sender import MidiError, open_sender
    from synth_ai.registry import CALIBRATION_DIRS

    cfg = _config(config)
    adapter = get_adapter(cfg.synth)
    if not isinstance(adapter, ParameterCatalog):
        raise _fail(ValueError(f"{cfg.synth} はパラメータ表を持っていません"))

    if parameter_id is None:
        typer.echo("測れるパラメータ（ID / 測る特徴 / 範囲）:")
        for p in adapter.calibratable_parameters():
            typer.echo(
                f"  {p.parameter_id}  {p.calibration_feature}  {p.min:g}〜{p.max:g}  {p.label}"
            )
        return

    info = adapter.parameter_info(parameter_id)
    if info is None or not info.is_numeric or info.min is None or info.max is None:
        raise _fail(ValueError(f"数値のパラメータ「{parameter_id}」がパラメータ表にありません"))
    try:
        target = Feature(feature or info.calibration_feature or "")
    except ValueError as exc:
        raise _fail(ValueError(f"測る特徴を --feature で指定してください（{feature}）")) from exc
    try:
        points = (
            tuple(float(v) for v in values.split(","))
            if values
            else _default_values(info.min, info.max)
        )
    except ValueError as exc:
        raise _fail(
            ValueError(f"--values はカンマ区切りの数値で指定してください: {values}")
        ) from exc
    out_of_range = [v for v in points if not info.min <= v <= info.max]
    if out_of_range:
        raise _fail(
            ValueError(f"範囲 {info.min:g}〜{info.max:g} の外の値があります: {out_of_range}")
        )

    note_name = note or cfg.test_note.note
    hold_s = max(hold or cfg.test_note.hold_s, MIN_HOLD_S.get(target, 0.0))
    tail_s = max(
        cfg.test_note.release_tail_s if tail is None else tail, MIN_TAIL_S.get(target, 0.0)
    )
    try:
        settings = CaptureSettings(
            note=note_to_midi(note_name),
            velocity=velocity or cfg.test_note.velocity,
            hold_s=hold_s,
            release_tail_s=tail_s,
            pre_roll_s=cfg.capture.pre_roll_s,
            fade_ms=cfg.capture.fade_ms,
            peak_warn_dbfs=cfg.capture.peak_warn_dbfs,
            quiet_warn_dbfs=cfg.capture.quiet_warn_dbfs,
        )
    except ValueError as exc:
        raise _fail(exc) from exc
    auto_conditions = (
        f"{note_name} / velocity {settings.velocity} / hold {hold_s:g}s / tail {tail_s:g}s"
    )
    plan = CalibrationPlan(
        synth_id=adapter.synth_id,
        parameter_id=info.parameter_id,
        parameter_label=info.label,
        feature=target,
        values=points,
        conditions=f"{conditions} / {auto_conditions}" if conditions else auto_conditions,
    )
    unit = UNITS[target]
    session_dir = (
        Path("runs")
        / "calibration"
        / f"{info.parameter_id}__{target.value}-{datetime.now():%Y%m%d-%H%M%S}"
    )
    typer.echo(f"パラメータ: {info.label}（{info.source_ref or '出典なし'}）")
    typer.echo(f"測る特徴: {LABELS[target]}（{unit}） / 値: {', '.join(f'{v:g}' for v in points)}")
    typer.echo(f"条件: {plan.conditions}")
    typer.echo("基準の音色を選び、このパラメータだけを変えてください。\n")

    use_midi = not manual and cfg.midi.output_port is not None
    try:
        recorder = SoundDeviceRecorder(
            cfg.capture.input_device, cfg.capture.sample_rate, cfg.capture.channels
        )
        sender_ctx = (
            open_sender(cfg.midi.output_port, cfg.midi.channel)  # type: ignore[arg-type]
            if use_midi
            else nullcontext(None)
        )
        with sender_ctx as sender:

            def ask_to_set(index: int, value: float) -> Step:
                answer = (
                    typer.prompt(
                        f"[{index + 1}/{len(points)}] {info.label} を {value:g} にして Enter"
                        "（s: スキップ / q: ここで終了）",
                        default="",
                        show_default=False,
                    )
                    .strip()
                    .lower()
                )
                return {"s": Step.SKIP, "q": Step.QUIT}.get(answer, Step.GO)

            def record(value: float, attempt: int) -> Path:
                result = capture_note(recorder, sender, settings, prompt=typer.echo)
                for w in result.warnings:
                    typer.secho(f"  注意: {w}", fg=typer.colors.YELLOW)
                return write_capture(session_dir / f"v{value:g}_try{attempt}.wav", result)

            def confirm(m: Measurement) -> Verdict:
                shown = (
                    "測れませんでした" if m.feature_value is None else f"{m.feature_value:g} {unit}"
                )
                typer.echo(f"  → {LABELS[target]}: {shown}")
                for issue in m.issues:
                    typer.secho(f"  注意: {issue.message}", fg=typer.colors.YELLOW)
                answer = (
                    typer.prompt(
                        "  Enter: 採用 / r: 録り直し / s: この値は使わない",
                        default="",
                        show_default=False,
                    )
                    .strip()
                    .lower()
                )
                return {"r": Verdict.RETRY, "s": Verdict.SKIP}.get(answer, Verdict.ACCEPT)

            session = run_session(
                plan, ask_to_set, record, lambda p: analyze_file(p).analysis, confirm
            )
    except (CaptureError, MidiError, AudioLoadError) as exc:
        raise _fail(exc) from exc

    typer.echo("\n値 → 特徴:")
    for m in session.points:
        typer.echo(f"  {m.parameter_value:>6g} → {m.feature_value:g} {unit}")
    if session.skipped:
        typer.echo(f"  使わなかった値: {', '.join(f'{v:g}' for v in session.skipped)}")
    try:
        curve = build_curve(session)
    except NotEnoughPointsError as exc:
        raise _fail(exc) from exc
    if not curve.is_monotonic:
        typer.secho(
            "注意: 値を上げても特徴が一方向に変わっていません。"
            "この曲線はレシピの逆引きに使われません。"
            "測定条件や測る特徴を見直してください",
            fg=typer.colors.YELLOW,
        )

    out_dir = CALIBRATION_DIRS.get(
        adapter.synth_id, Path("data") / f"{adapter.synth_id}_calibration"
    )
    path = out_dir / curve_filename(info.parameter_id, target)
    if path.exists() and not overwrite and not typer.confirm(f"{path} を上書きしますか？"):
        alt = session_dir / path.name
        save_json(curve, alt)
        typer.echo(f"上書きせず、{alt} に保存しました")
    else:
        save_json(curve, path)
        typer.echo(f"保存しました: {path}")
    typer.echo(f"録音: {session_dir}")
    typer.echo(
        "基準の音色に戻すため、変えたパラメータを保存せずに U-CC000 などを選び直してください"
    )


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
