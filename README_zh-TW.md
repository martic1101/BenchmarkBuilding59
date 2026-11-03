# Building 59 資料轉換 Benchmark

這套 benchmark 用來測試模型、代理系統或資料轉換方法：根據來源資料範例和 5 列目標表格，產生能轉換其他日期資料的程式，再以標準答案評分。

包含 601 題（293 題開發集、308 題保留測試集），所有題目使用的資料片段都已附上，無須另外下載完整 Building 59 原始資料。這是 `Building59-Benchmark-v2` 的獨立發布版本。

| 題型 | 內容 | dev | held_out |
|---|---|---:|---:|
| Type1 | 時間聚合 | 133 | 134 |
| Type2 | 單位轉換 | 34 | 31 |
| Type3 | 多檔案聚合與時間合併 | 85 | 83 |
| Type4 | 依設備或樓層分組，再聚合 | 41 | 60 |

## 安裝

Python 3.10 以上。在終端機執行：

```sh
git clone https://github.com/martic1101/BenchmarkBuilding59.git
cd BenchmarkBuilding59
python -m venv .venv
```

Windows PowerShell 啟用環境：`.venv\Scripts\Activate.ps1`；Linux/macOS：`source .venv/bin/activate`。

```sh
python -m pip install -r requirements.txt
```

提示詞產生與評分不需要 API key；模型呼叫由使用者自己的系統處理。

## 測試自己的系統

1. 先閱讀 [評估規格](evaluation_protocol.md)。用 `dev/` 調整方法，定案後才使用 `held_out/`。
2. 產生提示詞，例如：

   ```sh
   python runners/build_prompt.py held_out/Type4/Case001 none
   ```

   支援 `none`、`full_kb`、`selected_facts` 三種知識條件。`selected_facts` 是人工挑選正確事實的 oracle 上限，不代表真實檢索器結果。請分開報告各條件。
3. 將提示詞交給自己的模型或系統，將回覆中的 Python 程式存為 `my_solution.py`（去除 Markdown 程式碼圍欄）。程式介面為：

   ```python
   def transform(sources: dict) -> pandas.DataFrame:
       ...
   ```

   `sources` 是 CSV 檔名到本機路徑的字典。程式只能依輸入資料計算，回傳包含 `timestamp` 和指定目標欄位的 DataFrame；完整介面要求會寫在提示詞中。
4. 執行並評分：

   ```sh
   python evaluator/evaluate.py --case held_out/Type4/Case001 --program my_solution.py
   ```

   `--program` 會執行程式，使用普通子程序而非安全沙箱；模型產生的程式請在隔離環境內執行。也可由自己的系統產生 CSV，再單純評分：

   ```sh
   python evaluator/evaluate.py --case held_out/Type4/Case001 --pred my_output.csv
   ```

## 批次比較

將自己的預測 CSV 依題號存放，例如 `predictions/held_out/Type4/Case001.csv`，再執行：

```sh
python evaluator/evaluate_batch.py --predictions predictions --split held_out --type Type4 --out results/type4.json
```

拿掉 `--type Type4` 可評估整個 split。缺交、無法讀取或無法解析的預測以零分計入，分母固定為所選題目總數。輸出包括通過率、每題平均欄位正確率、每題平均數值正確率；完整 JSON 也包含逐題結果。

`exact_match` 要求欄位集合與時間戳完全一致、所有數值在 `1e-6 + 1e-3 × |標準答案|` 容差內。欄位順序和時間格式的輸出契約另行報告，詳見評估規格。

## 輸入與答案的界線

- `input/`：可提供給模型的範例和目標 schema。
- `kg/`：依知識條件提供的背景知識。
- `hidden/source_test/`：只在執行轉換程式時讀取，不提供給模型生成答案。
- `hidden/ground_truth.csv`、`reference_solution.py`、`task.json` 等：只供評分或研究核對，不提供給待測系統。

**不要讓模型或 agent 直接瀏覽整個 repo。** 請在另一個工作目錄只放允許的輸入。此 repo 的 `held_out` 是公開測試集，答案也已公開，並不是有伺服器保密的競賽測試集；使用者須自行維持評估隔離。

## 引用與授權

原始資料來源、論文引用和授權詳見 [英文 README](README.md#data-source)、[程式碼 MIT 授權](LICENSE) 和 [資料 CC BY 4.0 授權](LICENSE-DATA)。請同時引用原始 Building 59 資料集，並在報告中註明此 repo 的 commit、split、題型、知識條件、模型版本和評估設定。
