import numpy as np
import matplotlib.pyplot as plt

# 1. Сетка значений t на отрезке [-pi, pi]
t = np.linspace(-np.pi, np.pi, 1000)

# 2. Нулевое приближение x^(0)(t) = 0
x = np.zeros_like(t)

plt.figure(figsize=(10, 6), dpi=120)
plt.plot(t, x, '--', label=r'$x^{(0)}(t) = 0$', color='gray', alpha=0.6)

# 3. Выполнение 20 итераций
n_iter = 20
for k in range(1, n_iter + 1):
    x = (t + 1) * np.cos(x / 6.0) + np.sin(3 * t)

    # Отображаем ключевые итерации для демонстрации сходимости
    if k in [1, 2, 3, 5, 20]:
        lw = 2.5 if k == 20 else 1.2
        style = '-' if k == 20 else '--'
        plt.plot(t, x, style, label=f'$x^{{({k})}}(t)$', linewidth=lw)

# 4. Оформление графика
plt.title(r'Приближённое решение $x^{(20)}(t)$ методом простых итераций (Вариант 11)', fontsize=12)
plt.xlabel(r'$t$', fontsize=11)
plt.ylabel(r'$x(t)$', fontsize=11)
plt.xlim([-np.pi, np.pi])
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper left', fontsize=10)
plt.tight_layout()

# Сохранение и показ
plt.savefig('solution_variant_11.png', dpi=300)
plt.show()
