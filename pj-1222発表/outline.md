# スライド設計（本編20枚＋予備10枚）

編集は下の YAML ブロックのみを更新してください。

```yaml
slides:
  - id: S01
    title: 中国社会信用システムの制度アーキテクチャ
    layout: title
    bullets:
      - 卒業論文発表
      - 2025-12-22
      - 濱田 圭吾
    sources:
      - chapters/00_intro.md

  - id: S02
    title: 発表の流れ
    bullets:
      - 問題意識と研究課題
      - 分析枠組み（4軸）
      - 中国SCSの構造
      - 企業信用の作用
      - 比較と提案
    sources:
      - chapters/00_intro.md

  - id: S03
    title: 問題意識：信用評価の拡張
    bullets:
      - 信用評価が金融から行動へ拡大
      - 制度設計が統治権力に直結
      - 便益と副作用が同時に発生
    sources:
      - chapters/00_intro.md

  - id: S04
    title: 研究の問いと貢献
    bullets:
      - RQ1：4軸で制度構造を記述
      - RQ2：便益と副作用の条件を検討
      - RQ3：日本の設計選択肢を導出
    sources:
      - chapters/00_intro.md

  - id: S05
    title: 分析枠組み：4軸モデル
    layout: figure
    bullets:
      - 制度要素を4軸で分解
      - 対象は個人/企業で区別
    figure:
      label: 4軸モデル（概念図）
    sources:
      - chapters/00_intro.md
      - ４軸分析.md

  - id: S06
    title: SCSの定義と誤解の整理
    bullets:
      - 単一スコアではなく信用記録
      - 行政・司法・商取引まで対象
      - 守信優遇/失信制約が連動
    sources:
      - chapters/01_china.md

  - id: S07
    title: 導入動機と政策目的
    bullets:
      - Trust Deficitと法執行不全
      - 情報分断を是正し予防的統治
      - 2014年綱要が全国設計図
    sources:
      - chapters/01_china.md

  - id: S08
    title: 制度の変遷① 萌芽〜枠組形成
    bullets:
      - 1990s 三角債問題と金融信用DB
      - 2002-07 全国構想/指導意見
      - 2013 征信条例と司法ブラック
    sources:
      - chapters/01_china.md

  - id: S09
    title: 制度の変遷② 拡大〜調整
    bullets:
      - 2014 綱要で全国展開
      - 2015-18 パイロットと基盤整備
      - 2021以降 法治化と調整局面
    sources:
      - chapters/01_china.md

  - id: S10
    title: 主要プラットフォーム
    bullets:
      - 信用中国：失信/守信の公開窓口
      - NECIPS：企業登録と処分の公示
      - NCISP：省庁データ統合ハブ
    sources:
      - chapters/01_china.md

  - id: S11
    title: 肯定的評価：市場規律と効率
    bullets:
      - 守信激励/失信约束で信用水準↑
      - 取引コスト削減と金融包摂
      - パイロットで過剰投資を抑制
    sources:
      - chapters/01_china.md

  - id: S12
    title: 批判的評価：構造的リスク
    bullets:
      - 監視インフラ化と信用概念の拡張
      - 逆適応・社会的排除の発生
      - 不利益の不可視化と過剰制裁
    sources:
      - chapters/01_china.md

  - id: S13
    title: 2020年以降の調整局面
    bullets:
      - 道徳スコア型の運用縮小
      - 信用情報の目録化と基準統一
      - 便益重視と法制化の推進
    sources:
      - chapters/01_china.md
      - chapters/02_chibis_score.md

  - id: S14
    title: 中国SCSの4軸（要約）
    layout: two-column
    bullets: []
    left_title: ガバナンス/データ
    left_bullets:
      - NDRC・PBOC・法院の多主体統括
      - NCISP→信用中国/NECIPSで共有
    right_title: インセンティブ/官民
    right_bullets:
      - 連合懲戒とレッド/ブラック
      - 民間信用サービスは補助的
    sources:
      - chapters/01_china.md
      - chapters/02_chibis_score.md

  - id: S15
    title: 商務誠信とは
    bullets:
      - 企業信用の制度領域
      - 個人スコアとは切り分け
      - 市場秩序と遵法を目的化
    sources:
      - chapters/02_chibis_score.md

  - id: S16
    title: 企業信用の制度運用（4軸要約）
    layout: two-column
    bullets: []
    left_title: ガバナンス/データ
    left_bullets:
      - NDRC・PBOC・法院・SAMRが連携
      - 双公示→NCISP→信用中国で公開
    right_title: インセンティブ/官民
    right_bullets:
      - 入札・融資・許認可に連動
      - CRA/業界団体が運用を補完
    sources:
      - chapters/02_chibis_score.md

  - id: S17
    title: 企業行動への影響（選択圧）
    bullets:
      - コンプライアンス投資の強化
      - 失信コスト上昇で行動変化
      - 司法判断の実効性が上昇
    sources:
      - chapters/02_chibis_score.md

  - id: S18
    title: 副作用と救済策
    bullets:
      - 過剰適応・萎縮と汚職誘発
      - 誤登録と不利益の不可視化
      - 信用修復や手続整備が進展
    sources:
      - chapters/02_chibis_score.md

  - id: S19
    title: 国際参照と日本の現状
    bullets:
      - 米国：市場主導/FCRAの枠組み
      - EU：権利保護/GDPRの制約
      - 日本：CIC/JICC分立と課題
    sources:
      - chapters/03_japanscore.md
      - chapters/04_EUUSAcompare.md

  - id: S20
    title: 日本への示唆と提案
    bullets:
      - 分散統合型/準公共APIハブ
      - 透明性・救済・監査を最小要件
      - 権限集中を避け便益を確保
    sources:
      - chapters/06_proposal.md

  - id: APPENDIX-01
    title: 付録：年表（詳細）
    layout: figure
    bullets:
      - 1990s〜2025の制度変遷
    figure:
      label: 年表（詳細版）
    sources:
      - chapters/01_china.md

  - id: APPENDIX-02
    title: 付録：4軸モデルの定義
    bullets:
      - 軸1 ガバナンス：基準と責任
      - 軸2 データフロー：収集と統合
      - 軸3 インセンティブ：賞罰と修復
      - 軸4 官民関係：役割分担と連携
    sources:
      - ４軸分析.md

  - id: APPENDIX-03
    title: 付録：ガバナンス詳細
    bullets:
      - NDRCが統括、連席会議を運営
      - PBOCが金融信用DBを管理
      - 最高法院が失信被執行人を公開
      - SAMRが企業情報公示を担当
    sources:
      - chapters/02_chibis_score.md

  - id: APPENDIX-04
    title: 付録：データフロー詳細
    bullets:
      - 双公示で行政情報を公開
      - NCISPに集約し全国で共有
      - 信用中国/NECIPSで閲覧可能
      - 企業IDで名寄せと同期
    sources:
      - chapters/02_chibis_score.md

  - id: APPENDIX-05
    title: 付録：インセンティブ詳細
    bullets:
      - ブラックリストで参入制限
      - レッドリストで手続優遇
      - 共同懲戒で制裁が横断化
      - 信用修復で再参加を可能化
    sources:
      - chapters/02_chibis_score.md

  - id: APPENDIX-06
    title: 付録：官民関係の例
    bullets:
      - CRAが信用評価を補助
      - 芝麻信用は公的評価外
      - 業界団体が内部懲戒を運用
      - プラットフォームが情報提供
    sources:
      - chapters/02_chibis_score.md

  - id: APPENDIX-07
    title: 付録：逆適応の具体像
    bullets:
      - オーバーコンプライアンス
      - 違反隠しや汚職誘発の懸念
      - 地域差で対応コストが増大
      - 中小企業ほど負担が重い
    sources:
      - chapters/02_chibis_score.md

  - id: APPENDIX-08
    title: 付録：調整局面の政策
    bullets:
      - 2021 信用情報目録の制定
      - 2022 社会信用法草案を公表
      - 2024-25 便益重視の指針
      - 省級条例の整備が進行
    sources:
      - chapters/01_china.md
      - chapters/02_chibis_score.md

  - id: APPENDIX-09
    title: 付録：日本の設計要件（MVP）
    bullets:
      - 目的制限と比例性の明確化
      - 最小データと本人コントロール
      - 開示・説明・異議申立て
      - 監査ログと標準API
    sources:
      - chapters/06_proposal.md

  - id: APPENDIX-10
    title: 付録：主要出典
    bullets:
      - Liang et al. 2018 / Bi 2021
      - 2014-2020 綱要 / MERICS 2021
      - 主要政策文書・報告書
      - 参考文献一覧を参照
    sources:
      - refs/references.md
      - refs/bassui.md
```
