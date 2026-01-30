def solve_grid_full_algorithmic(h, v):
    # ПУНКТ 1: Всего путей (простая динамика)
    grid_total = [[0] * (h + 1) for _ in range(v + 1)]
    grid_total[0][0] = 1
    
    for i in range(v + 1):
        for j in range(h + 1):
            if i > 0: grid_total[i][j] += grid_total[i-1][j]
            if j > 0: grid_total[i][j] += grid_total[i][j-1]
            
    total_result = grid_total[v][h]

    # ПУНКТ 2: Без двух вертикальных подряд
    # Здесь в каждой клетке храним два значения:
    # [пути, пришедшие ГОРИЗОНТАЛЬНО, пути, пришедшие ВЕРТИКАЛЬНО]
    # dp[v][h] = [count_h, count_v]
    dp = [[[0, 0] for _ in range(h + 1)] for _ in range(v + 1)]
    
    # Начальная точка: считаем, что мы «пришли» горизонтально, чтобы можно было начать с вертикали
    dp[0][0][0] = 1 
    
    for i in range(v + 1):
        for j in range(h + 1):
            # 1. Считаем пути, приходящие ГОРИЗОНТАЛЬНО (j > 0)
            # Сюда можно прийти после ЛЮБОГО шага (и после h, и после v)
            if j > 0:
                dp[i][j][0] = dp[i][j-1][0] + dp[i][j-1][1]
            
            # 2. Считаем пути, приходящие ВЕРТИКАЛЬНО (i > 0)
            # Сюда можно прийти ТОЛЬКО если предыдущий шаг был ГОРИЗОНТАЛЬНЫМ
            if i > 0:
                dp[i][j][1] = dp[i-1][j][0]
                
    restricted_result = sum(dp[v][h])
    
    return total_result, restricted_result

h, v = 20, 17
total, restricted = solve_grid_full_algorithmic(h, v)

print(f"1. Всего путей (алгоритмически): {total:,}")
print(f"2. Без двух вертикальных подряд (алгоритмически): {restricted:,}")
