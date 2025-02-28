from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import json
import uuid
from pydantic import BaseModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Разрешаем запросы с любого источника
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к BSL LS (скачай JAR-файл из https://github.com/1c-syntax/bsl-language-server/releases)
BSL_LS_PATH = "./bsl-language-server.jar"

class CodeRequest(BaseModel):
    code: str

@app.post('/analyze')
async def analyze(request: CodeRequest):
    code = request.code
    
    # Создаем временную папку и файл
    temp_dir = os.path.join("temp", f"temp_{uuid.uuid4()}")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, "temp.bsl")

    try:
        # Сохраняем код во временный файл
        with open(temp_file_path, "w", encoding="utf-8") as file:
            file.write(code)

        # Запускаем BSL LS
        result = subprocess.run(
            ["java", "-Xms512m", "-Xmx1024m", "-XX:+UseSerialGC", "-jar", BSL_LS_PATH, "--analyze", "--srcDir", temp_dir, "--outputDir", temp_dir, "--reporter", "json"],
            capture_output=True,
            text=True,
            timeout=30  # Таймаут 30 секунд
        )

        # Читаем результат из JSON-файла
        report_path = os.path.join(temp_dir, "bsl-json.json")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as report_file:
                report = json.load(report_file)

            # Обрабатываем диагностики
            errors = []
            for file_info in report.get("fileinfos", []):
                for diagnostic in file_info.get("diagnostics", []):
                    start_line = diagnostic["range"]["start"]["line"] + 1  # Нумерация с 1
                    message = diagnostic["message"]
                    code_description = diagnostic.get("codeDescription", {}).get("href", "#")
                    
                    # Формируем строку с ошибкой и ссылкой
                    error_message = f"Line {start_line}: {message} <a href='{code_description}' target='_blank'>[Подробнее]</a>"
                    errors.append(error_message)

            # Сортируем ошибки по номеру строки
            errors.sort(key=lambda x: int(x.split(" ")[1].strip(':')))
        else:
            errors = ["Ошибка: Отчет не найден"]
           
    except Exception as e:
        errors = [f"Ошибка: {str(e)}"]

    finally:
        # Удаляем временные файлы
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)

    return {"errors": errors}

# Маршрут для отдачи favicon.ico
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")
    
# Маршрут для отдачи index.html
@app.get("/")
async def index():
    return FileResponse("static/index.html")
    
# Отдача других статических файлов (CSS, JS)
@app.get("/{path:path}")
async def static_files(path: str):
    file_path = os.path.join("static", path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(f"static/{path}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
