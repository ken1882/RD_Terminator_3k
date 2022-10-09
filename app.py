import _G
import os
import json
from flask import Flask, make_response, redirect, abort
from flask import render_template,jsonify,send_from_directory,request
from _G import log_error,log_info,log_warning,log_debug
from flask_config import DevelopmentConfig,ProductionConfig
from datetime import datetime,timedelta
import novelai as nai
from random import randint


app = Flask(__name__)
app.initialized = False

LONG_MAX_VAL = 0xffffffff

PermissionData = {'0': {}}
NaiGenCache = {
    '_': {
        'quota': 0,
        'ttl': datetime.now()
    }
}

### Helpers

def application_reload():
    global PermissionData
    nai.reload()
    with open(_G.PERM_FILE, 'r') as fp:
        PermissionData = json.load(fp)

### Routes
@app.route('/rdt3k/api/RequestNaiImage', methods=['POST'])
def request_nai_image():
    token = request.form.get('token')
    pdat = next((d for d in PermissionData['0']['NAI_ALLOWED_KEYS'] if d['Secret'] == token), None)
    if not pdat:
        return jsonify({'msg': 'Forbidden'}),403

    if token not in NaiGenCache:
        NaiGenCache[token] = {
            'quota': 0,
            'ttl': datetime.now()+timedelta(seconds=pdat['Duration'])
        }
    
    cdat = NaiGenCache[token]
    if cdat['quota'] > pdat['Limit']:
        print(datetime.now(), cdat['ttl'])
        if datetime.now() >= cdat['ttl']:
            NaiGenCache[token]['quota'] = 0
            cdat['ttl'] = datetime.now() + timedelta(seconds=pdat['Duration'])
        else:
            return jsonify({'msg': 'Try after '+str(cdat['ttl'])}),429

    tags  = request.form.get('tags')
    seed  = request.form.get('seed')
    steps = request.form.get('steps')
    scale = request.form.get('scale')
    sampler = request.form.get('sampler')
    model = request.form.get('model')
    ucp = request.form.get('ucp')
    uc = request.form.get('uc')
    
    if not tags:
        return jsonify({'msg': 'Bad tags'}),400

    kwargs = {}
    if seed:
        try:
            kwargs['seed'] = int(seed)
        except Exception:
            pass
    else:
        seed = randint(0, LONG_MAX_VAL)
        kwargs['seed'] = seed
    
    if steps:
        try:
            kwargs['steps'] = int(steps)
        except Exception:
            pass
    if scale:
        try:
            kwargs['scale'] = int(scale)
        except Exception:
            pass
    if sampler:
        kwargs['sampler'] = sampler
    if model:
        kwargs['model'] = model
    if uc:
        kwargs['uc'] = uc
    if ucp:
        try:
            kwargs['ucp'] = int(ucp)
        except Exception:
            pass

    log_info("Generation extra arguments:", kwargs)
    NaiGenCache[token]['quota'] += 1
    ret = nai.generate_image(tags, **kwargs)
    if ret == _G.ERRNO_BADDATA:
        return jsonify({'msg': 'Bad paramters'}),400
    elif ret == _G.ERRNO_FAILED:
        return jsonify({'msg': 'Server error'}),500

    return jsonify({'data': ret, 'seed': seed}),200

@app.route('/rdt3k/api/ReloadConfig', methods=['POST'])
def reload_config():
    token = request.form.get('token')
    _pk   = os.getenv('FLASK_REFRESH_KEY')
    if not _pk or token != os.getenv('FLASK_REFRESH_KEY'):
        return jsonify({'msg': 'Forbidden'}),403
    application_reload()
    return jsonify(PermissionData),200

if not app.initialized:
    app.initialized = True
    application_reload()
    if _G.PRODUCTION:
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

if __name__ == '__main__':
    try:
        app.run()
    finally:
        _G.FlagRunning = False