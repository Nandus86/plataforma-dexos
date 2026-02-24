import time
import os

def update_version():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    version_file = os.path.join(current_dir, "VERSION")
    
    timestamp = int(time.time())
    new_version = f"0.0.1.{timestamp}"
    
    with open(version_file, "w", encoding="utf-8") as f:
        f.write(new_version)
        
    print(f"Versão atualizada para: {new_version}")

if __name__ == "__main__":
    update_version()
