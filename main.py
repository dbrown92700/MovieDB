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

with open('movies.csv', 'r') as movie_file:
    lines = movie_file.readlines()
movie_list = []
values = ['id', 'title', 'image', 'rating', 'plot', 'genres']
for item in lines:
    movie_list.append({values[i]: item.split(',')[i].rstrip('\n') for i in range(len(values))})
now = datetime.now()
os.rename('movies.csv', f'movies{now.month:02}{now.day:02}{now.year:02}-{now.hour:02}{now.minute:02}.csv')


def write_movie_file():

    global movie_list

    with open('movies.csv', 'w') as mov_file:
        for movie in movie_list:
            mov_file.write(','.join(movie.values()) + '\n')


write_movie_file()


@app.route('/')
def list_movies():

    global movie_list

    genre = request.args.get('genre') or 'All'
    name = request.args.get('name') or ''
    if name:
        name = name.split(' ')
    movie_table = ''
    for movie in movie_list:
        genres = movie['genres'].split(':')
        if (genre == 'All') or (genre in genres):
            match = True
            if name:
                for term in name:
                    if term.lower() not in movie['title'].lower():
                        match = False
            if match:
                movie_table += f'<tr>\n \
                        <td width=200>\
                        <a href="https://imdb.com/title/{movie["id"]}/" target="_imdb">{movie["title"]}</a>\n \
                        <br><br><br><div align=center><a href="/delete?id={movie["id"]}">delete</a></div></td>\n \
                        <td width=90 align=left><img src="{movie["image"]}" height=120 width=80></td>\n \
                        <td width=30>{movie["rating"]}</td>\n \
                        <td width=500 style="border: 1px solid black;">{movie["plot"].replace("~^",",")}</td>\n \
                        <td width=80>'
                for this in movie["genres"].split(':'):
                    movie_table += f'<a href="/?genre={this}">{this}</a><br>\n'
                movie_table += '</td></tr>'
    return render_template('list_movies.html', genre=genre, name=' '.join(name), movie_table=Markup(movie_table))


@app.route('/search')
def search():

    return render_template('search.html')


@app.route('/results')
def search_result():

    api_key = os.environ.get('IMDB_API_KEY')
    search_text = request.args.get("search_text").replace('+', '%20')
    results = json.loads(requests.get(f'https://imdb-api.com/en/API/Search/{api_key}/{search_text}').text)

    page = '<html>\n\
           <head>\n\
           <meta charset="UTF-8">\n\
           <meta name="viewport" content="width=400">\
           <title>IMDB Search</title>\
           </head>\
           <body><br>\n\
           Search results for: <b>{results["expression"]}</b><br>\n\
           <table>\n'
    for result in results['results']:
        page += f'<tr>\n \
                <td width=200><a href="https://imdb.com/title/{result["id"]}/" target="_imdb">{result["title"]}<br> \
                {result["description"]}</a></td>\n \
                <td width=100 align=left><img src="{result["image"]}" height=120 width=80></td>\n \
                <td width=50><a href="/add?id={result["id"]}">Add</a></td>\n'
    page += '</body></html>'

    return Markup(page)


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
    new_movie = {'id': imdb_id, 'title': title['fullTitle'], 'image': title['image'], 'rating': title['imDbRating'],
                 'plot': title['plot'].replace(',', '~^'), 'genres': genres}
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

    return redirect('/')


@app.route('/delete')
def delete_movie():

    global movie_list

    imdb_id = request.args.get("id")
    for movie in movie_list:
        if movie['id'] == imdb_id:
            movie_list.pop(movie_list.index(movie))
    write_movie_file()
    return redirect('/')


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='192.168.1.59', port=8080, debug=True)
# [END gae_python38_app]
