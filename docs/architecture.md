# アーキテクチャ

```
cli.py / registry.py（アプリケーション層: Adapter を選んで注入）
        │
core/（機種非依存）── adapters/base.py（SynthAdapter 契約・Capabilities）
        ▲                         ▲
        └──── adapters/fake.py, adapters/kronos2/（契約を実装）
infrastructure/（MIDI・録音の共通転送。adapters に依存しない）
```

- データの流れ: `reference.wav → AudioAnalysis → SoundSpec → SynthAdapter.create_recipe() → PatchRecipe`
- `core/workflow/recipe.py` の `generate_recipe` は Adapter の返したレシピを契約検証する
  （synth_id・sound_spec_id の一致、手順番号、サンプル取り込み可否、エンジン名）。
- 境界は `tests/architecture/import_rules.py` が AST で検査する。
