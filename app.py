from flask import Flask, render_template, request, jsonify
import requests
import json
import os
import random
from deep_translator import GoogleTranslator

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'chave_secreta_quiz_123'

RANKING_FILE = 'ranking.json'
translator = GoogleTranslator(source='en', target='pt')

def get_questions(selected_categories, difficulty='medio'):
    diff_map = {"facil": "easy", "medio": "medium", "dificil": "hard"}
    api_diff = diff_map.get(difficulty, "medium")

    raw_questions = []
    if not selected_categories:
        selected_categories = ["9"]

    per_category = max(5, 30 // len(selected_categories))

    for cat_id in selected_categories:
        url = f"https://opentdb.com/api.php?amount={per_category}&category={cat_id}&difficulty={api_diff}&type=multiple"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get('response_code') == 0:
                    raw_questions.extend(data.get('results', []))
        except:
            continue

    if not raw_questions:
        return []

    random.shuffle(raw_questions)
    final_list = raw_questions[:15]

    # Tradução em Lote (Batch) para ser rápido
    try:
        to_translate = []
        for q in final_list:
            to_translate.append(q['question'])
            to_translate.append(q['correct_answer'])
            to_translate.extend(q['incorrect_answers'])

        mega_string = " ||| ".join(to_translate)
        translated_mega = translator.translate(mega_string)
        translated_parts = translated_mega.split(" ||| ")

        idx = 0
        for q in final_list:
            if idx + 4 < len(translated_parts):
                q['question'] = translated_parts[idx]
                q['correct_answer'] = translated_parts[idx+1]
                q['incorrect_answers'] = [
                    translated_parts[idx+2],
                    translated_parts[idx+3],
                    translated_parts[idx+4]
                ]
                idx += 5
    except Exception as e:
        print(f"Erro na tradução: {e}")

    return final_list

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    difficulty = request.form.get('difficulty', 'medio')
    selected_cats = request.form.getlist('categories')
    questions = get_questions(selected_cats, difficulty)
    
    if not questions:
        return "Nenhuma questão encontrada para os filtros selecionados.", 404
        
    return render_template('game.html', questions=questions, difficulty=difficulty)

@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
        
    ranking = []
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r') as f:
            try:
                ranking = json.load(f)
            except:
                ranking = []
    
    ranking.append({"name": data.get('name', 'Anônimo'), "score": data.get('score', 0)})
    ranking = sorted(ranking, key=lambda x: x['score'], reverse=True)[:10]
    
    with open(RANKING_FILE, 'w') as f:
        json.dump(ranking, f, indent=4)
        
    return jsonify({"status": "success"})

@app.route('/ranking')
def ranking():
    data = []
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r') as f:
            try:
                data = json.load(f)
            except:
                data = []
    return render_template('ranking.html', ranking=data)

if __name__ == '__main__':
    app.run(debug=True)