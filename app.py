import os
from flask import Flask, request, jsonify, send_from_directory
from models import db, Photo
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ------------------- Setup -------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))   # Project root
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')      # uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'photos.db')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# ------------------- Routes -------------------

@app.route('/api/photos', methods=['GET', 'POST'])
def photos():
    if request.method == 'GET':
        photos = Photo.query.order_by(Photo.uploaded_at.desc()).all()
        return jsonify([p.to_dict() for p in photos])
    
    # POST -> Upload new photos
    files = request.files.getlist('photos')
    directory = request.form.get('directory', '')
    tags = request.form.get('tags', '')
    description = request.form.get('description', '')

    saved = []
    for f in files:
        filename = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Collision handling
        base, ext = os.path.splitext(filename)
        i = 1
        while os.path.exists(path):
            filename = f"{base}_{i}{ext}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            i += 1

        f.save(path)
        url = f'/api/uploads/{filename}'
        photo = Photo(filename=filename, filepath=path, url=url, directory=directory, tags=tags, description=description)
        db.session.add(photo)
        saved.append(photo)

    db.session.commit()
    return jsonify([p.to_dict() for p in saved]), 201

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/photos/<int:photo_id>', methods=['GET','PUT','DELETE'])
def photo_detail(photo_id):
    p = Photo.query.get_or_404(photo_id)

    if request.method == 'GET':
        return jsonify(p.to_dict())

    elif request.method == 'PUT':
        # Support both JSON PUT and multipart/form-data (for reupload)
        if request.content_type.startswith("multipart/form-data"):
            tags = request.form.get('tags')
            description = request.form.get('description')
            new_file = request.files.get('photo')

            if tags is not None:
                p.tags = ','.join(tags.split(',')) if isinstance(tags, str) else tags

            if description is not None:
                p.description = description

            if new_file:
                # Delete old file
                if os.path.exists(p.filepath):
                    os.remove(p.filepath)

                filename = secure_filename(new_file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                i = 1
                while os.path.exists(path):
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{i}{ext}"
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    i += 1
                new_file.save(path)
                p.filename = filename
                p.filepath = path
                p.url = f'/api/uploads/{filename}'
        else:
            # JSON PUT (tags & description)
            data = request.json
            if 'tags' in data:
                p.tags = ','.join(data['tags'])
            if 'description' in data:
                p.description = data['description']

        db.session.commit()
        return jsonify(p.to_dict())

    elif request.method == 'DELETE':
        # Delete file if exists
        try:
            if os.path.exists(p.filepath):
                os.remove(p.filepath)
        except Exception:
            pass
        db.session.delete(p)
        db.session.commit()
        return '', 204

@app.route('/api/photos/search')
def search_photos():
    q = request.args.get('q','').lower()
    if not q:
        return jsonify([])
    results = Photo.query.filter(
        (Photo.tags.ilike(f'%{q}%')) |
        (Photo.description.ilike(f'%{q}%')) |
        (Photo.filename.ilike(f'%{q}%')) |
        (Photo.directory.ilike(f'%{q}%'))
    ).order_by(Photo.uploaded_at.desc()).all()
    return jsonify([r.to_dict() for r in results])

# ------------------- Main -------------------
if __name__ == '__main__':
    app.run(debug=True)
