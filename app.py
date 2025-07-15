from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_FILE = 'database.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(article_id) REFERENCES articles(id)
            )
        ''')

@app.route('/', methods=['GET'])
def index():
    keyword = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    with sqlite3.connect(DB_FILE) as conn:
        if keyword:
            cursor = conn.execute("""
                SELECT id, title, created_at FROM articles
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (f'%{keyword}%', f'%{keyword}%', per_page + 1, offset))
        else:
            cursor = conn.execute("""
                SELECT id, title, created_at FROM articles
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page + 1, offset))
        articles = cursor.fetchall()

    has_more = len(articles) > per_page
    articles = articles[:per_page]

    return render_template('index.html', articles=articles, keyword=keyword, page=page, has_more=has_more)

@app.route('/add', methods=['POST'])
def add_article():
    title = request.form['title']
    content = request.form['content']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO articles (title, content, created_at) VALUES (?, ?, ?)",
                     (title, content, created_at))
    return redirect(url_for('index'))

@app.route('/article/<int:article_id>', methods=['GET', 'POST'])
def article_detail(article_id):
    # 文章详情页面，同时处理新增评论
    if request.method == 'POST':
        comment = request.form.get('comment')
        if comment:
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("INSERT INTO comments (article_id, content, created_at) VALUES (?, ?, ?)",
                             (article_id, comment, created_at))
        return redirect(url_for('article_detail', article_id=article_id))

    with sqlite3.connect(DB_FILE) as conn:
        article = conn.execute("SELECT title, content, created_at FROM articles WHERE id=?", (article_id,)).fetchone()
        comments = conn.execute("SELECT id, content, created_at FROM comments WHERE article_id=? ORDER BY created_at ASC", (article_id,)).fetchall()

    return render_template('article.html', article=article, comments=comments, article_id=article_id)

@app.route('/article/<int:article_id>/edit', methods=['GET', 'POST'])
def article_edit(article_id):
    if request.method == 'POST':
        new_title = request.form.get('edit_title')
        new_content = request.form.get('edit_content')
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("UPDATE articles SET title=?, content=? WHERE id=?", (new_title, new_content, article_id))
        return redirect(url_for('article_detail', article_id=article_id))

    with sqlite3.connect(DB_FILE) as conn:
        article = conn.execute("SELECT title, content FROM articles WHERE id=?", (article_id,)).fetchone()

    return render_template('article_edit.html', article=article, article_id=article_id)

@app.route('/article/delete/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM articles WHERE id=?", (article_id,))
        conn.execute("DELETE FROM comments WHERE article_id=?", (article_id,))
    return redirect(url_for('index'))

@app.route('/comment/delete/<int:comment_id>/<int:article_id>', methods=['POST'])
def delete_comment(comment_id, article_id):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    return redirect(url_for('article_detail', article_id=article_id))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
