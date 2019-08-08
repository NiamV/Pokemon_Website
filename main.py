import os
import requests
import traceback
from flask import Flask
import asyncio
app = Flask(__name__)

from flask import render_template

all_types = ["normal",
    "fire",
    "fighting",
    "water",
    "flying",
    "grass",
    "poison",
    "electric",
    "ground",
    "psychic",
    "rock",
    "ice",
    "bug",
    "dragon",
    "ghost",
    "dark",
    "steel",
    "fairy",
]

colours = {
    "normal": "#A8A878",
    "fire": "#F08030",
    "fighting": "#C03028",
    "water": "#6890F0",
    "flying": "#A890F0",
    "grass": "#78C850",
    "poison": "#A040A0",
    "electric": "#F8D030",
    "ground": "#E0C068",
    "psychic": "#F85888",
    "rock": "#B8A038",
    "ice": "#98D8D8",
    "bug": "#A8B820",
    "dragon": "#7038F8",
    "ghost": "#705898",
    "dark": "#705848",
    "steel": "#B8B8D0",
    "fairy": "#EE99AC",
}

def response(move):
    if move['version_group_details'][0]['move_learn_method']['name'] == "level-up":
        level = move['version_group_details'][0]['level_learned_at']
    else:
        level = " "
        # continue
    return {
        'url': requests.get(move['move']['url']),
        'method': move['version_group_details'][0]['move_learn_method']['name'],
        'level': level
    }

@app.route('/pokemon/')
@app.route('/pokemon/<name>')
def pokemon(name=None):    
    try:
        import time
        s = time.perf_counter()        
        r = requests.get('https://pokeapi.co/api/v2/pokemon/' + name)
        data = r.json()

        abilities = []
        for ability in data['abilities']:
            ability_response = requests.get(ability['ability']['url'])
            ability_json = ability_response.json()

            effects = []
            for effect in ability_json['effect_entries']:
                effects.append(effect['effect'])

            effects_string = ", ".join(effects)

            abilities.append({
                "name": ability['ability']['name'].title(), 
                "effect": effects_string,
                "isHidden": ability['is_hidden']})

        stats = []
        for stat in data['stats']:
            stats.append(stat['base_stat'])

        types = []
        type1 = {"name": data['types'][0]['type']['name'].title(), "colour": colours[data['types'][0]['type']['name']]}
        if len(data['types']) == 2:
            type2 = {"name": data['types'][1]['type']['name'].title(), "colour": colours[data['types'][1]['type']['name']]}
            if data['types'][0]['slot'] == 2:
                types.append(type2)
                types.append(type1)
            else:
                types.append(type1)
                types.append(type2)
        else:
            types.append(type1)
        
        weaknesses = {
            "normal": 1,
            "fire": 1,
            "fighting": 1,
            "water": 1,
            "flying": 1,
            "grass": 1,
            "poison": 1,
            "electric": 1,
            "ground": 1,
            "psychic": 1,
            "rock": 1,
            "ice": 1,
            "bug": 1,
            "dragon": 1,
            "ghost": 1,
            "dark": 1,
            "steel": 1,
            "fairy": 1,
        }
        
        for item in types:
            r_type = requests.get('https://pokeapi.co/api/v2/type/' + item['name'].lower())
            type_json = r_type.json()

            for weakness in type_json['damage_relations']['double_damage_from']:
                weaknesses[weakness['name']] *= 2

            for weakness in type_json['damage_relations']['half_damage_from']:
                weaknesses[weakness['name']] *= 0.5

            for weakness in type_json['damage_relations']['no_damage_from']:
                weaknesses[weakness['name']] *= 0


        moves = []
        async def main():
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(
                    None, 
                    response, 
                    move
                )
                for move in data['moves']
            ]
            for move_response in await asyncio.gather(*futures):
                move_json = move_response['url'].json()

                if move_json['power'] == None:
                    power = "-"
                else:
                    power = move_json['power']

                if move_json['accuracy'] == None:
                    accuracy = "-"
                else:
                    accuracy = move_json['accuracy']

                moves.append({
                    'name': move_json['name'].title().replace("-", " "),
                    'type': {'name': move_json['type']['name'].title(), 'colour': colours[move_json['type']['name']]},
                    'class': move_json['damage_class']['name'],
                    'method': move_response['method'].replace("-", " "),
                    'level': move_response['level'],
                    'power': power,
                    'accuracy': accuracy,
                    'pp': move_json['pp']
                })

        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())

        moves_sorted = sorted(moves, key = lambda i:(i['method'],i['level']))

        elapsed = time.perf_counter() - s
        print(f"{__file__} executed in {elapsed:0.2f} seconds.")

        try:
            r2 = requests.get('https://pokeapi.co/api/v2/pokemon-species/' + name)
            data2 = r2.json()

            egg = data2['egg_groups'][0]['name'].title()
            if len(data2['egg_groups']) == 2:
                egg += " and "
                egg += data2['egg_groups'][1]['name'].title()


            other_stats = {
                'base_experience': data['base_experience'],
                'base_happiness': data2['base_happiness'],
                'egg_groups': egg,
                'egg_cycles': data2['hatch_counter'],
                'growth_rate': data2['growth_rate']['name'].title().replace("-", " "),
                'colour': data2['color']['name'].title(),
                'shape': data2['shape']['name'].title(),
                'height': str(float(data['height'])/10) + " m",
                'weight': str(float(data['weight'])/10) + " kg",   
            }
        except:
            other_stats = {
                'base_experience': "-",
                'base_happiness': "-",
                'egg_groups': "-",
                'egg_cycles': "-",
                'growth_rate': "-",
                'colour': "-",
                'shape': "-",
                'height': "-",
                'weight': "-"   
            } 

        return render_template(
            'pokemon.html', 
            name=data['name'].title().replace("-", " "), 
            number = data['id'],
            all_types = all_types,
            types = types,
            weaknesses = weaknesses, 
            data = data, 
            abilities = abilities, 
            stats = stats,
            moves = moves_sorted,
            other = other_stats)
        
    except Exception:
        traceback.print_exc()
        return render_template('404.html', name=name.title())

# port = int(os.environ.get('PORT', 5000))
# app.run(port = port)