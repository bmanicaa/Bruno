"""
META-LABELING SCREENING (Fase 1)

Avalia se um modelo simples consegue separar trades bons de ruins com features
de entrada (RSI 1d, ATR%, ADX BTC, stop dist, classe, regime, direcao).

Walk-forward honesto: para cada bloco OOS, treina apenas com janelas ANTERIORES
(IS p/ OOS1; IS+OOS1 p/ OOS2; ...), prevê no bloco e filtra trades com
probabilidade abaixo do threshold. IS cross-val AUC reporta se existe sinal
aprendível.

ATENCAO: filtro pos-hoc aproxima o efeito (sem recomposicao de capital/breakers).
Se promissor, implementar o filtro NATIVAMENTE no motor e re-validar com
walk-forward + bootstrap antes de qualquer adocao.

Uso: python scripts/meta_label.py --exp 9ea2dff4 [--threshold 0.5]
"""

import argparse
import json
import os
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP_DIR = os.path.join(BASE_DIR, 'data', 'experimentos')
OOS_NAMES = ['OOS1', 'OOS2', 'OOS3', 'OOS4']
FEATURES = ['rsi_1d', 'atr_1d_pct', 'btc_adx_1d', 'stop_dist_pct',
            'asset_class', 'regime_macro', 'direction']
CATEGORICAL = ['asset_class', 'regime_macro', 'direction']


def load_experiment(hash_or_path):
    if os.path.exists(hash_or_path):
        with open(hash_or_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    with open(os.path.join(EXP_DIR, f'exp_{hash_or_path}.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def build_matrix(trades):
    raw = [[t.get(f, 0.0) for f in FEATURES] for t in trades]
    if not raw:
        return None, None
    x = np.zeros((len(raw), len(FEATURES)), dtype=float)
    for j, f in enumerate(FEATURES):
        if f in CATEGORICAL:
            vals = sorted({r[j] for r in raw})
            x[:, j] = [vals.index(r[j]) for r in raw]
        else:
            x[:, j] = [float(r[j]) for r in raw]
    y = np.array([1.0 if t['pnl_brl'] > 0 else 0.0 for t in trades])
    return x, y


def make_models(seed=42):
    return {
        'logreg': LogisticRegression(C=1.0, class_weight='balanced', max_iter=2000,
                                     random_state=seed),
        'rf': RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                     class_weight='balanced', random_state=seed, n_jobs=-1),
    }


def metrics_of(trades, kept_mask=None):
    if kept_mask is not None:
        trades = [t for t, k in zip(trades, kept_mask) if k]
    if not trades:
        return None
    pnl = np.array([t['pnl_brl'] for t in trades])
    risk = np.array([max(t['risk_brl'], 1e-9) for t in trades])
    wins = pnl > 0
    gross_p = pnl[wins].sum()
    gross_l = -pnl[~wins].sum()
    pf = gross_p / gross_l if gross_l > 1e-12 else float('inf')
    return {
        'n': len(trades),
        'pnl': float(pnl.sum()),
        'win_rate': float(wins.mean() * 100),
        'pf': float(pf),
        'expectancy_r': float((pnl / risk).mean()),
    }


def evaluate(summary, threshold=0.5, seed=42):
    detail = summary.get('windows_detail', {})
    print('config:', summary.get('config_hash'), '| params:',
          json.dumps(summary.get('config', {}), ensure_ascii=False))

    all_trades = []
    for name in OOS_NAMES:
        all_trades.extend(detail.get(name, {}).get('trades', []))
    x_all, y_all = build_matrix(all_trades)

    for model_name, model in make_models(seed).items():
        print('\n=== MODELO:', model_name, '| threshold p>%.2f ===' % threshold)
        scaler = StandardScaler()
        train_windows = []
        kept_flags = []
        for name in OOS_NAMES:
            train_trades = []
            for w in train_windows:
                train_trades.extend(detail.get(w, {}).get('trades', []))
            x_tr, y_tr = build_matrix(train_trades)
            oos_trades = detail.get(name, {}).get('trades', [])
            x_ts, y_ts = build_matrix(oos_trades)
            row = {'window': name}
            if x_tr is None or len(y_tr) < 8 or len(set(y_tr)) < 2 or x_ts is None:
                row.update({'treinado': False, 'base': metrics_of(oos_trades),
                            'filtrado': None, 'auc': None})
                kept_flags.append(np.ones(len(oos_trades), dtype=bool))
                train_windows.append(name)
                print_row(row)
                continue
            x_tr_s = scaler.fit_transform(x_tr)
            x_ts_s = scaler.transform(x_ts)
            model.fit(x_tr_s, y_tr)
            prob = model.predict_proba(x_ts_s)[:, 1]
            keep = prob >= threshold
            row.update({
                'treinado': True,
                'base': metrics_of(oos_trades),
                'filtrado': metrics_of(oos_trades, keep),
                'keep_pct': float(keep.mean() * 100),
                'auc': float(roc_auc_score(y_ts, prob)) if len(set(y_ts)) > 1 else None,
            })
            kept_flags.append(keep)
            train_windows.append(name)
            print_row(row)

        base_all = metrics_of(all_trades)
        filt_all = metrics_of(all_trades, np.concatenate(kept_flags))
        print('AGREGADO OOS | base: n=%d pnl=%.0f PF=%.2f win=%.1f%% expR=%+.3f | filtrado: n=%d pnl=%.0f PF=%.2f win=%.1f%% expR=%+.3f' % (
            base_all['n'], base_all['pnl'], base_all['pf'], base_all['win_rate'], base_all['expectancy_r'],
            filt_all['n'], filt_all['pnl'], filt_all['pf'], filt_all['win_rate'], filt_all['expectancy_r']))

        if x_all is not None and len(set(y_all)) > 1:
            x_s = StandardScaler().fit_transform(x_all)
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            aucs = cross_val_score(model, x_s, y_all, cv=cv, scoring='roc_auc')
            print('AUC IS cross-val (5-fold): %.3f +/- %.3f (sinal global dos features)' % (
                float(aucs.mean()), float(aucs.std())))


def print_row(row):
    b, f = row['base'], row['filtrado']
    bs = 'n=%3d pnl=%8.0f PF=%4.2f win=%4.1f%% expR=%+5.3f' % (
        b['n'], b['pnl'], b['pf'], b['win_rate'], b['expectancy_r']) if b else 'sem trades'
    if f:
        fs = 'n=%3d pnl=%8.0f PF=%4.2f win=%4.1f%% expR=%+5.3f (keep %4.1f%%)' % (
            f['n'], f['pnl'], f['pf'], f['win_rate'], f['expectancy_r'], row.get('keep_pct', 0))
    else:
        fs = 'nao treinado'
    print('%-6s | base: %s | filtrado: %s | auc=%s' % (
        row['window'], bs, fs, ('%.3f' % row['auc']) if row.get('auc') is not None else 'n/a'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp', required=True)
    parser.add_argument('--threshold', type=float, default=0.5)
    args = parser.parse_args()
    summary = load_experiment(args.exp)
    evaluate(summary, threshold=args.threshold)


if __name__ == '__main__':
    main()
