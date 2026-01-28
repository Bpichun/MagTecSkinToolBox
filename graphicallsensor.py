import numpy as np
import matplotlib.pyplot as plt
import time, os

plt.ion()

MAX_POINTS = 100
file_path = "campo_global.txt"
num_sensores = 15

# ---- Crear figura con grilla 3x5 ----
fig, axes = plt.subplots(3, 5, figsize=(18, 10))
axes = axes.flatten()  # Facilita indexar [0..14]

lines = []
data_buffers = []

for i in range(num_sensores):
    ax = axes[i]

    line_x, = ax.plot([], [], 'r-', label='X', linewidth=1.2)
    line_y, = ax.plot([], [], 'g-', label='Y', linewidth=1.2)
    line_z, = ax.plot([], [], 'b-', label='Z', linewidth=1.2)

    ax.set_title(f"Sensor {i+1}")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("B [μT]")
    ax.grid(True)
    ax.legend(fontsize=8)
    ax.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))

    lines.append((line_x, line_y, line_z))
    data_buffers.append(([], [], []))

plt.tight_layout()

# ---- Loop en tiempo real ----
while True:
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            data = np.genfromtxt(file_path, dtype=float)

            if data.ndim == 1:
                data = data[np.newaxis, :]

            for i in range(min(num_sensores, data.shape[0])):
                Bx, By, Bz = data[i]
                x_vals, y_vals, z_vals = data_buffers[i]

                x_vals.append(Bx)
                y_vals.append(By)
                z_vals.append(Bz)

                if len(x_vals) > MAX_POINTS:
                    x_vals[:] = x_vals[-MAX_POINTS:]
                    y_vals[:] = y_vals[-MAX_POINTS:]
                    z_vals[:] = z_vals[-MAX_POINTS:]

                t = np.arange(len(x_vals))

                lines[i][0].set_data(t, x_vals)
                lines[i][1].set_data(t, y_vals)
                lines[i][2].set_data(t, z_vals)

                axes[i].set_xlim(max(0, len(t) - MAX_POINTS), len(t))

                y_all = np.concatenate([x_vals, y_vals, z_vals])
                y_min, y_max = np.min(y_all), np.max(y_all)
                margin = 0.1 * (y_max - y_min + 1e-9)
                axes[i].set_ylim(y_min - margin, y_max + margin)

            fig.canvas.draw()
            fig.canvas.flush_events()

        time.sleep(0.01)

    except KeyboardInterrupt:
        print("Interrumpido por el usuario.")
        break
    except Exception as e:
        print("Error:", e)
        time.sleep(0.5)
