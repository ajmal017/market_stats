DIRECTIONAL_DOLLARS = 10000 # for a 10 volatility ratio
NEUTRAL_DOLLARS = DIRECTIONAL_DOLLARS * 5

def directional_contract_number(stock_price, vol_ratio):
	return DIRECTIONAL_DOLLARS / (stock_price * vol_ratio)

def neutral_contract_number(stock_price, vol_ratio):
	return NEUTRAL_DOLLARS / (stock_price * 100 * vol_ratio)