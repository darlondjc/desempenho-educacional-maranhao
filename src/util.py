import time
import threading

# ── CONTROLE DE TIMER ───────────────────
_timer_stop = False

def timer():
	global _timer_stop
	inicio = time.time()
	_timer_stop = False
	
	while not _timer_stop:
		decorrido = int(time.time() - inicio)
		minutos = decorrido // 60
		segundos = decorrido % 60
		print(f"\rTempo: {minutos:02d}:{segundos:02d}", end="", flush=True)
		time.sleep(1)
	print()  # Quebra de linha ao finalizar

def start_timer():
	timer_thread = threading.Thread(target=timer, daemon=True)
	timer_thread.start()
	return timer_thread

def stop_timer(timer_thread):
	global _timer_stop
	_timer_stop = True
	if timer_thread:
		timer_thread.join(timeout=2)