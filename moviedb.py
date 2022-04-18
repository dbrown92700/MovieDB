#!/usr/bin/python3

__author__ = "David Brown <dbrown92700@gmail.com>"
__contributors__ = []

import requests
from flask import Flask, request, render_template, redirect
from markupsafe import Markup
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'any random string'

db_path = os.environ.get('MOVIE_DB_PATH')
app_url = os.environ.get('SCRIPT_NAME')

with open(f'{db_path}/movies.csv', 'r') as movie_file:
    lines = movie_file.readlines()
movie_list = []
values = ['id', 'title', 'image', 'rating', 'plot', 'genres', 'watched', 'available']
for item in lines:
    movie_list.append({values[i]: item.split(',')[i].rstrip('\n') for i in range(len(values))})
now = datetime.now()
os.rename(f'{db_path}/movies.csv', f'{db_path}/movies{now.month:02}{now.day:02}{now.year:02}-{now.hour:02}{now.minute:02}.csv')


def write_movie_file():

    global movie_list

    with open(f'{db_path}/movies.csv', 'w') as mov_file:
        for movie in movie_list:
            mov_file.write(','.join(movie.values()) + '\n')


write_movie_file()


@app.route('/')
def list_movies():

    global movie_list

    genre = request.args.get('genre') or 'All'
    name = request.args.get('name') or ''
    page = int(request.args.get('page') or '1')
    watched = request.args.get('watched') or ''
    available = request.args.get('available') or ''

    print(f'Page {page}')

    if name:
        name = name.split(' ')
    else:
        name = []

    match_list = []
    full_genre_list = []
    for movie in movie_list:
        genres = movie['genres'].split(':')
        for genre_item in genres:
            if genre_item not in full_genre_list:
                full_genre_list.append(genre_item)
        if genre not in (genres + ['All']):
            continue
        if watched and (watched != movie['watched']):
            continue
        if available and (available != movie['available']):
            continue
        if name:
            for term in name:
                if term.lower() in movie['title'].lower():
                    match_list.append(movie)
                    break
        else:
            match_list.append(movie)

    movie_table = ''
    first = (page-1)*10
    last = min(page*10, len(match_list))
    for movie in match_list[first:last]:
        movie_table += f'<tr>\n' \
                       f'<td width=200>' \
                       f'<a href="https://imdb.com/title/{movie["id"]}/" target="_imdb">' \
                       f'{movie["title"].replace("~^", ",")}</a>\n' \
                       f'<br><br><br><div align=center><a href="{app_url}/edit?id={movie["id"]}">Edit</a></div></td>\n' \
                       f'<td width=90 align=left><img src="{movie["image"]}" height=120 width=80></td>\n' \
                       f'<td width=30>{movie["rating"]}</td>\n' \
                       f'<td width=300 style="border: 1px solid black;">\n' \
                       f'<div style="height:120px;width:300px;overflow:auto;">' \
                       f'{movie["plot"].replace("~^",",")}</td>\n<td width=100>'
        for this in movie["genres"].split(':'):
            movie_table += f'{this}<br>\n'
        movie_table += f'<br>Watched: {movie["watched"].title()}<br>Available: {movie["available"].title()}</td></tr>'

    genre_menu = ''
    full_genre_list.sort()
    for genre_item in full_genre_list:
        selected = ''
        if genre == genre_item:
            selected = ' selected'
        genre_menu += f'<option value="{genre_item}"{selected}>{genre_item}</option>\n'

    watched_radio = ''
    for choice in ['yes', 'no']:
        selected = ''
        if choice == watched:
            selected = 'checked'
        watched_radio += f'<td>{choice.title()} <input type="radio" name="watched" value="{choice}" {selected}></td>'

    available_radio = ''
    for choice in ['yes', 'no']:
        selected = ''
        if choice == available:
            selected = 'checked'
        available_radio += f'<td>{choice.title()} <input type="radio" name="available"' \
                           f'value="{choice}" {selected}></td>'

    url = f'{app_url}/?name={"+".join(name)}&genre={genre}&watched={watched}&available={available}'

    pages = f'<td width="350" align="center">Movies {first+1}-{last} of {len(match_list)} movies</td>\n' \
            f'<td width="350" align="center">'
    if page == 1:
        pages += 'prev<<<'
    else:
        pages += f'<a href="{url}&page={page-1}">prev<<< </a>'
    pages += f' <b>Page {page}</b> '
    if len(match_list) > page*10:
        pages += f'<a href="{url}&page={page+1}"> >>>next</a></td>\n'
    else:
        pages += '>>>next</td>\n'

    return render_template('list_movies.html', genre_menu=Markup(genre_menu), watched_radio=Markup(watched_radio),
                           available_radio=Markup(available_radio), name=' '.join(name), pages=Markup(pages),
                           movie_table=Markup(movie_table), app_url=app_url)


@app.route('/search')
def search():

    return render_template('search.html', app_url=app_url)


@app.route('/results')
def search_result():

    api_key = os.environ.get('IMDB_API_KEY')
    search_text = request.args.get("search_text").replace('+', '%20')
    results = json.loads(requests.get(f'https://imdb-api.com/en/API/Search/{api_key}/{search_text}').text)

    if results['results'] is None:
        return render_template('error.html', err=results, key=api_key, app_url=app_url)

    expression = results["expression"]
    movie_table = ''
    for result in results['results']:
        movie_table += f'<tr>\n \
                <td width=200><a href="https://imdb.com/title/{result["id"]}/" target="_imdb">{result["title"]}<br> \
                {result["description"]}</a></td>\n \
                <td width=100 align=left><img src="{result["image"]}" height=120 width=80></td>\n \
                <td width=50><a href="{app_url}/add?id={result["id"]}">Add</a></td>\n'

    return render_template('search_result.html', expression=expression, movie_table=Markup(movie_table),
                           app_url=app_url)


@app.route('/add')
def add_movie():

    global movie_list
    imdb_id = request.args.get("id")
    api_key = os.environ.get('IMDB_API_KEY')

    url = f'https://imdb-api.com/en/API/Title/{api_key}/{imdb_id}'
    print(url)

    title = json.loads(requests.get(url).text)

    print(json.dumps(title, indent=2))

    genres = title['genres'].split(',')
    genres = ':'.join([genres[x].lstrip(' ') for x in range(len(genres))])
    new_movie = {'id': imdb_id, 'title': title['fullTitle'].replace(',', '~^'), 'image': title['image'],
                 'rating': title['imDbRating'], 'plot': title['plot'].replace(',', '~^'), 'genres': genres,
                 'watched': 'no', 'available': 'yes'}
    found = False
    for movie in movie_list:
        if movie['id'] == new_movie['id']:
            movie_list[movie_list.index(movie)] = new_movie
            found = True
            break
        if float(new_movie['rating']) > float(movie['rating']):
            movie_list.insert(movie_list.index(movie), new_movie)
            found = True
            break
    if not found:
        movie_list.append(new_movie)

    write_movie_file()

    return redirect(f'/edit?id={imdb_id}')


@app.route('/edit')
def edit_movie():

    global movie_list

    imdb_id = request.args.get("id")
    for movie in movie_list:
        if movie['id'] == imdb_id:
            break
    movie_table = f'<tr>\n' \
                  f'<td width=200><a href="https://imdb.com/title/{movie["id"]}/" target="_imdb">' \
                  f'{movie["title"].replace("~^",",")}</a></td>\n' \
                  f'<td width=90 align=left><img src="{movie["image"]}" height=120 width=80></td>\n' \
                  f'<td width=30>{movie["rating"]}</td>\n' \
                  f'<td width=300 style="border: 1px solid black;">\n' \
                  f'<div style="height:120px;width:300px;overflow:auto;">{movie["plot"].replace("~^", ",")}</td>\n' \
                  f'<td width=80>'
    for this in movie["genres"].split(':'):
        movie_table += f'{this}<br>\n'
    movie_table += f'</td></tr></table>\n'

    watched_radio = ''
    for choice in ['yes', 'no']:
        selected = ''
        if choice == movie['watched']:
            selected = 'checked'
        watched_radio += f'<td width="50">{choice.title()} ' \
                         f'<input type="radio" name="watched" value="{choice}" {selected}></td>'

    available_radio = ''
    for choice in ['yes', 'no']:
        selected = ''
        if choice == movie['available']:
            selected = 'checked'
        available_radio += f'<td>{choice.title()} ' \
                           f'<input type="radio" name="available" value="{choice}" {selected}></td>'

    return render_template('edit_movie.html', title=movie['title'], movie_table=Markup(movie_table),
                           watched_radio=Markup(watched_radio), available_radio=Markup(available_radio),
                           id=movie['id'], app_url=app_url)


@app.route('/delete')
def delete_movie():

    global movie_list

    imdb_id = request.args.get("id")
    for movie in movie_list:
        if movie['id'] == imdb_id:
            list_index = movie_list.index(movie)
            movie_list.pop(list_index)
    write_movie_file()

    return redirect('/')


@app.route('/save')
def save_movie():

    global movie_list

    imdb_id = request.args.get("id")
    watched = request.args.get("watched")
    available = request.args.get("available")

    print(f'ID:{imdb_id} Watched:{watched} Available: {available}')

    for movie in movie_list:
        if movie['id'] == imdb_id:
            list_index = movie_list.index(movie)
            movie_list[list_index]['watched'] = watched
            movie_list[list_index]['available'] = available
    write_movie_file()
    print(list_index)
    return redirect('/')


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='192.168.1.59', port=8080, debug=True)
# [END gae_python38_app]
