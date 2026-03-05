from flask import Flask, render_template, request, jsonify, session
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

    per_category = max(1, 25 // len(selected_categories))

    for cat_id in selected_categories:
        url = f"https://opentdb.com/api.php?amount={per_category}&category={cat_id}&difficulty={api_diff}&type=multiple"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                raw_questions.extend(res.json().get('results', []))
        except:
            continue

    if not raw_questions:
        return []

    random.shuffle(raw_questions)

    # TRADUÇÃO APENAS DAS PERGUNTAS (Mais rápido!)
    try:
        # Extrai apenas os enunciados
        questions_only = [q['question'] for q in raw_questions]

        # Traduz o bloco de enunciados
        mega_text = " || ".join(questions_only)
        translated_mega = translator.translate(mega_text)
        translated_list = translated_mega.split(" || ")

        # Devolve as perguntas traduzidas para o objeto original
        for i, q in enumerate(raw_questions):
            if i < len(translated_list):
                q['question'] = translated_list[i]

    except Exception as e:
        print(f"Erro na tradução: {e}")

    return raw_questions


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_game', methods=['POST'])
def start_game():
    difficulty = request.form.get('difficulty', 'medio')
    selected_cats = request.form.getlist('categories')
    questions = get_questions(selected_cats, difficulty)
    return render_template('game.html', questions=questions, difficulty=difficulty)


@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    ranking = []
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r') as f:
            ranking = json.load(f)
    ranking.append({"name": data.get('name'), "score": data.get('score')})
    ranking = sorted(ranking, key=lambda x: x['score'], reverse=True)[:10]
    with open(RANKING_FILE, 'w') as f:
        json.dump(ranking, f)
    return jsonify({"status": "success"})


@app.route('/ranking')
def ranking():
    data = []
    if os.path.exists(RANKING_FILE):
        with open(RANKING_FILE, 'r') as f:
            data = json.load(f)
    return render_template('ranking.html', ranking=data)


if __name__ == '__main__':
    app.run(debug=True)
