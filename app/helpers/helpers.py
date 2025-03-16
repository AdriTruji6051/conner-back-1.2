def profit_percentage(cost: float, sale_price: float) -> int:
    if cost <= 0:
        raise ValueError('cost must be greater than zero')
    
    profit = sale_price - cost

    return int((profit / cost) * 100)