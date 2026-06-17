from src.config import KELLY_FRACTION

def calc_ev(our_prob, bookmaker_odds):
    if bookmaker_odds <= 1.0: return 0.0, 0.0, 0.0
    implied = 1 / bookmaker_odds
    ev      = (our_prob * bookmaker_odds) - 1
    edge    = our_prob - implied
    kelly   = (edge / (bookmaker_odds - 1)) * KELLY_FRACTION if edge > 0 else 0
    return round(ev, 4), round(edge, 4), round(kelly, 4)

def ev_flag(ev, edge):
    if edge >= 0.08:  return "🔥 STRONG BET"
    if edge >= 0.04:  return "✅ VALUE BET"
    if edge >= 0.01:  return "⚠️  MARGINAL"
    return "❌ NO VALUE"
