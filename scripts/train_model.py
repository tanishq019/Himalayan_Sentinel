"""Train using the Kaggle CSV. --dev-synthetic is only for local smoke testing."""
import argparse, json
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'flood_risk_dataset_india.csv'; MODELS=ROOT/'models'
BASE=['Latitude','Longitude','Rainfall_mm','Temperature_C','Humidity_pct','River_Discharge_m3_s','Water_Level_m','Elevation_m','Land_Cover','Soil_Type','Population_Density','Infrastructure','Historical_Floods']
ALIASES={'Rainfall (mm)':'Rainfall_mm','Temperature (°C)':'Temperature_C','Humidity (%)':'Humidity_pct','River Discharge (m³/s)':'River_Discharge_m3_s','Water Level (m)':'Water_Level_m','Elevation (m)':'Elevation_m','Land Cover':'Land_Cover','Soil Type':'Soil_Type','Population Density':'Population_Density','Historical Floods':'Historical_Floods','Flood Occurred':'Flood_Occurred'}

def dev_data(n=500):
 rng=np.random.default_rng(42); rain=rng.gamma(3,35,n); water=np.clip(rng.normal(2.8+rain/115,1,n),.2,12); discharge=np.clip(rng.normal(250+rain*4,130,n),10,1800); soil=rng.uniform(20,95,n)
 logit=-7+.023*rain+.62*water+.0015*discharge+.015*soil+rng.normal(0,.65,n); y=(logit>0).astype(int)
 return pd.DataFrame({'Latitude':rng.uniform(29,32,n),'Longitude':rng.uniform(76,80,n),'Rainfall_mm':rain,'Temperature_C':rng.uniform(-4,28,n),'Humidity_pct':rng.uniform(35,100,n),'River_Discharge_m3_s':discharge,'Water_Level_m':water,'Elevation_m':rng.uniform(400,4500,n),'Land_Cover':rng.choice(['Forest','Agriculture','Barren'],n),'Soil_Type':rng.choice(['Loamy','Clay','Sandy'],n),'Population_Density':rng.uniform(5,1000,n),'Infrastructure':rng.choice(['Low','Moderate','High'],n),'Historical_Floods':rng.binomial(1,.32,n),'Flood_Occurred':y})

def main():
 p=argparse.ArgumentParser(); p.add_argument('--dev-synthetic',action='store_true'); a=p.parse_args()
 if DATA.exists(): df=pd.read_csv(DATA).rename(columns=ALIASES); source='Kaggle Flood Risk Prediction Dataset in India (synthetic)'
 elif a.dev_synthetic: df=dev_data(); source='DEVELOPMENT-ONLY generated synthetic smoke-test data'; df.to_csv(ROOT/'data'/'development_only_synthetic.csv',index=False)
 else: raise SystemExit(f'Missing {DATA}. Download the Kaggle CSV and place it there, or use --dev-synthetic for local smoke testing only.')
 missing=[c for c in BASE+['Flood_Occurred'] if c not in df.columns]
 if missing: raise SystemExit(f'CSV is missing required columns: {missing}')
 print(f'Dataset loaded successfully\nRows: {len(df)}\nColumns: {list(df.columns)}\nTarget: Flood_Occurred\nClass distribution: {df["Flood_Occurred"].value_counts(dropna=False).to_dict()}')
 df=df[BASE+['Flood_Occurred']].copy(); df['Flood_Occurred']=pd.to_numeric(df['Flood_Occurred'],errors='coerce'); df=df.dropna(subset=['Flood_Occurred']); y=df.pop('Flood_Occurred').astype(int)
 num=df.select_dtypes(include=np.number).columns.tolist(); cat=[c for c in BASE if c not in num]
 prep=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median'))]),num),('cat',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore'))]),cat)])
 pipe=Pipeline([('preprocess',prep),('model',RandomForestClassifier(n_estimators=80,random_state=42,class_weight='balanced',n_jobs=1))])
 Xtr,Xte,ytr,yte=train_test_split(df,y,test_size=.2,random_state=42,stratify=y); pipe.fit(Xtr,ytr); pred=pipe.predict(Xte); prob=pipe.predict_proba(Xte)[:,1]
 pr,re,f1,_=precision_recall_fscore_support(yte,pred,average='binary',zero_division=0)
 metrics={'dataset_source':source,'rows':len(df),'accuracy':round(float(accuracy_score(yte,pred)),4),'precision':round(float(pr),4),'recall':round(float(re),4),'f1':round(float(f1),4),'roc_auc':round(float(roc_auc_score(yte,prob)),4),'confusion_matrix':confusion_matrix(yte,pred).tolist()}
 names=pipe.named_steps['preprocess'].get_feature_names_out(); importances=pipe.named_steps['model'].feature_importances_; fi=[{'feature':str(n).replace('num__','').replace('cat__',''),'importance':round(float(v),6)} for n,v in sorted(zip(names,importances),key=lambda x:x[1],reverse=True)]
 stats={c:{'mean':round(float(df[c].mean()),6),'median':round(float(df[c].median()),6),'std':round(float(df[c].std()),6),'min':round(float(df[c].min()),6),'max':round(float(df[c].max()),6),'percentiles':{str(q):round(float(df[c].quantile(q)),6) for q in [.05,.1,.25,.5,.75,.9,.95]}} for c in num}
 MODELS.mkdir(exist_ok=True); joblib.dump(pipe,MODELS/'flood_risk_model.joblib'); (MODELS/'metrics.json').write_text(json.dumps(metrics,indent=2)); (MODELS/'feature_importance.json').write_text(json.dumps(fi,indent=2)); (MODELS/'dataset_stats.json').write_text(json.dumps(stats,indent=2)); print(json.dumps(metrics,indent=2))
if __name__=='__main__': main()
