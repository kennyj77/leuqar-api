from fastapi import FastAPI
import sqlite3
import re

app = FastAPI()

def inicializar_banco_nuvem():
    conexao = sqlite3.connect("leuqar_nuvem.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS enciclopedia_fts USING fts5(
            titulo,
            conceito,
            funcionamento,
            exemplo,
            historico
        )
    """)
    # Exemplo inicial de teste na nuvem
    cursor.execute("SELECT count(*) FROM enciclopedia_fts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO enciclopedia_fts (titulo, conceito, funcionamento, exemplo, historico) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            "fotossíntese",
            "Fotossíntese é o processo bioquímico pelo qual plantas e outros organismos transformam luz solar em energia química.",
            "Ela funciona através de estruturas chamadas cloroplastos nas folhas, que capturam a luz solar e utilizam essa energia para converter dióxido de carbono e água em glicose e oxigênio.",
            "Um exemplo clássico no dia a dia é o cultivo de plantas em estufas ou vasos perto da janela, onde elas absorvem a luz do sol para crescer.",
            "O termo foi criado pelo cientista Charles Reid Barnes em 1893, embora o processo em si venha ocorrendo na Terra há bilhões de anos, sendo responsável por oxigenar a atmosfera do planeta."
        ))
    conexao.commit()
    conexao.close()

inicializar_banco_nuvem()

@app.get("/perguntar")
def perguntar(q: str):
    conexao = sqlite3.connect("leuqar_nuvem.db")
    cursor = conexao.cursor()
    
    texto_original = q.lower().strip()
    
    # Identifica o que o usuário quer saber
    if any(t in texto_original for t in ["como funciona", "como opera"]):
        coluna = "funcionamento"
    elif any(t in texto_original for t in ["exemplo", "dia a dia", "prática"]):
        coluna = "exemplo"
    elif any(t in texto_original for t in ["história", "quando surgiu", "origem", "quem criou", "período"]):
        coluna = "historico"
    else:
        coluna = "conceito"
        
    # Limpa o termo de busca
    termo = texto_original
    for r in ["o que é", "quem criou", "como funciona", "qual a história de", "fale sobre", "explique", "quando surgiu"]:
        if termo.startswith(r + " "):
            termo = termo[len(r)+1:].strip()
    termo = re.sub(r'[^\w\s]', '', termo).strip()
    
    if not termo:
        conexao.close()
        return {"resposta": "Não consegui identificar o termo na sua pergunta."}

    try:
        cursor.execute(f"SELECT {coluna} FROM enciclopedia_fts WHERE titulo LIKE ? LIMIT 1", (f"%{termo}%",))
        resultado = cursor.fetchone()
        conexao.close()
        
        if resultado and resultado[0]:
            return {"resposta": resultado[0]}
        return {"resposta": f"Ainda não tenho registros detalhados sobre '{termo}' na minha base remota."}
    except Exception as e:
        conexao.close()
        return {"resposta": "Ocorreu um erro ao processar sua consulta no servidor."}