export interface CodeStep {
  step: number;
  title: string;
  language: string;
  code: string;
}

export interface TemplateContext {
  artifactId: string;
  framework: "lightgbm" | "xgboost" | string;
  objective: string;
  numTrees: number;
  featureNames: string[];
  params: Record<string, unknown>;
}

function fmtFeatures(names: string[]): string {
  if (names.length === 0) return "[]  # feature names not available";
  const preview = names.slice(0, 8).map(n => `"${n}"`).join(", ");
  const tail = names.length > 8 ? `, ...  # ${names.length} total` : "";
  return `[${preview}${tail}]`;
}

function fmtParams(params: Record<string, unknown>): string {
  const KEEP = ["num_leaves", "max_depth", "learning_rate", "n_estimators",
                "num_boost_round", "subsample", "colsample_bytree",
                "min_child_samples", "lambda_l1", "lambda_l2", "reg_alpha", "reg_lambda"];
  const entries = Object.entries(params)
    .filter(([k]) => KEEP.includes(k))
    .map(([k, v]) => `    "${k}": ${JSON.stringify(v)},`)
    .join("\n");
  return entries || '    # (default params used)';
}

export function lightgbmSteps(ctx: TemplateContext): CodeStep[] {
  const isRanker = ctx.objective.includes("lambdarank") || ctx.objective.includes("rank");
  const metric = isRanker ? "ndcg" : ctx.objective.includes("binary") ? "binary_logloss" : "rmse";
  const objectiveParam = isRanker ? '"lambdarank"' : ctx.objective.includes("binary") ? '"binary"' : ctx.objective.includes("multiclass") ? '"multiclass"' : '"regression"';

  return [
    {
      step: 1,
      title: "Install dependencies",
      language: "bash",
      code: `pip install lightgbm pandas numpy scikit-learn cerebro-extractor`,
    },
    {
      step: 2,
      title: "Load your data",
      language: "python",
      code: `import pandas as pd

FEATURE_NAMES = ${fmtFeatures(ctx.featureNames)}

X_train = pd.read_csv("train_features.csv")[FEATURE_NAMES]
y_train = pd.read_csv("train_labels.csv").squeeze()${isRanker ? `
group_train = pd.read_csv("train_groups.csv").squeeze()  # query group sizes` : ""}`,
    },
    {
      step: 3,
      title: "Configure & train the booster",
      language: "python",
      code: `import lightgbm as lgb

params = {
${fmtParams(ctx.params)}
    "objective": ${objectiveParam},
    "metric": "${metric}",
    "verbosity": -1,
}

dtrain = lgb.Dataset(X_train, label=y_train${isRanker ? ", group=group_train.tolist()" : ""})
model = lgb.train(
    params,
    dtrain,
    num_boost_round=${ctx.numTrees || 100},
)`,
    },
    {
      step: 4,
      title: "Save & load the model",
      language: "python",
      code: `model.save_model("model.txt")

# Reload later:
model = lgb.Booster(model_file="model.txt")`,
    },
    {
      step: 5,
      title: "Extract artifact with Cerebro",
      language: "bash",
      code: `cerebro extract \\
  --model model.txt \\
  --samples train_features.csv \\
  --labels  train_labels.csv \\
  --output  artifact.json`,
    },
    {
      step: 6,
      title: "Ingest into Cerebro dashboard",
      language: "bash",
      code: `# Start the API server, then:
curl -s -X POST http://localhost:8000/artifacts \\
  -F "model=@model.txt" \\
  -F "model_name=my-lgbm-model" \\
  | jq .id`,
    },
  ];
}

export function xgboostSteps(ctx: TemplateContext): CodeStep[] {
  const isRanker = ctx.objective.includes("rank");
  const objectiveParam = isRanker ? "rank:ndcg" : ctx.objective.includes("binary") ? "binary:logistic" : ctx.objective.includes("multiclass") ? "multi:softmax" : "reg:squarederror";

  return [
    {
      step: 1,
      title: "Install dependencies",
      language: "bash",
      code: `pip install xgboost pandas numpy scikit-learn cerebro-extractor`,
    },
    {
      step: 2,
      title: "Load your data",
      language: "python",
      code: `import pandas as pd

FEATURE_NAMES = ${fmtFeatures(ctx.featureNames)}

X_train = pd.read_csv("train_features.csv")[FEATURE_NAMES]
y_train = pd.read_csv("train_labels.csv").squeeze()`,
    },
    {
      step: 3,
      title: "Configure & train the booster",
      language: "python",
      code: `import xgboost as xgb

params = {
${fmtParams(ctx.params)}
    "objective": "${objectiveParam}",
    "verbosity": 0,
}

dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=FEATURE_NAMES)
model = xgb.train(
    params,
    dtrain,
    num_boost_round=${ctx.numTrees || 100},
)`,
    },
    {
      step: 4,
      title: "Save & load the model",
      language: "python",
      code: `model.save_model("model.json")  # ubj or json format

# Reload later:
model = xgb.Booster()
model.load_model("model.json")`,
    },
    {
      step: 5,
      title: "Extract artifact with Cerebro",
      language: "bash",
      code: `cerebro extract \\
  --model model.json \\
  --samples train_features.csv \\
  --labels  train_labels.csv \\
  --output  artifact.json`,
    },
    {
      step: 6,
      title: "Ingest into Cerebro dashboard",
      language: "bash",
      code: `# Start the API server, then:
curl -s -X POST http://localhost:8000/artifacts \\
  -F "model=@model.json" \\
  -F "model_name=my-xgb-model" \\
  | jq .id`,
    },
  ];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function genericSteps(_ctx: TemplateContext): CodeStep[] {
  return [
    {
      step: 1,
      title: "Install Cerebro extractor",
      language: "bash",
      code: `pip install cerebro-extractor`,
    },
    {
      step: 2,
      title: "Extract artifact from your saved model",
      language: "python",
      code: `from cerebro.extractor import extract

artifact = extract(
    model_path="model_file",  # path to your saved model
    samples="train_features.csv",
    labels="train_labels.csv",
)
artifact.save("artifact.json")`,
    },
    {
      step: 3,
      title: "Ingest into Cerebro dashboard",
      language: "bash",
      code: `curl -s -X POST http://localhost:8000/artifacts \\
  -F "model=@model_file" \\
  -F "model_name=my-model" \\
  | jq .id`,
    },
  ];
}

export function getSteps(ctx: TemplateContext): CodeStep[] {
  const fw = ctx.framework.toLowerCase();
  if (fw.includes("lightgbm")) return lightgbmSteps(ctx);
  if (fw.includes("xgboost")) return xgboostSteps(ctx);
  return genericSteps(ctx);
}
