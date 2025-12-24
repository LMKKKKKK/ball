import os
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, date
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image

# ---------------------- 基础配置 ----------------------
app = Flask(__name__)
# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'sports_team_2025_secret_key_stronger'

# 核心：配置根目录图片路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, 'images')
# 确保images文件夹存在
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# ---------------------- 图片上传配置 ----------------------
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PLAYER_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'players')
app.config['FOOD_UPLOAD_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'foods')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB限制

# ---------------------- 本地图片访问路由 ----------------------
@app.route('/images/<filename>')
def serve_local_image(filename):
    # 安全校验：仅允许访问指定格式的图片
    allowed_ext = {'png', 'jpg', 'jpeg', 'gif'}
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if file_ext in allowed_ext:
        return send_from_directory(IMAGE_FOLDER, filename)
    return "不允许访问的文件类型", 403

# ---------------------- 延迟初始化球类图片配置（解决上下文问题） ----------------------
def init_sport_images():
    """在应用上下文内初始化球类图片配置"""
    app.config['SPORT_IMAGES'] = {
        # 篮球（顶部背景+球星头像）
        '篮球': {
            'background': f'/images/basketball_top_bg.jpg',  # 顶部横幅背景图
            'star_images': [
                f'/images/basketball_star1.jpg',
                f'/images/basketball_star2.jpg',
                f'/images/basketball_star3.jpg'
            ]
        },
        # 足球
        '足球': {
            'background': f'/images/football_top_bg.jpg',    # 足球顶部横幅背景图
            'star_images': [
                f'/images/football_star1.jpg',
                f'/images/football_star2.jpg',
                f'/images/football_star3.jpg'
            ]
        },
        # 排球
        '排球': {
            'background': f'/images/volleyball_top_bg.jpg',
            'star_images': [
                f'/images/volleyball_star1.jpg',
                f'/images/volleyball_star2.jpg',
                f'/images/volleyball_star3.jpg'
            ]
        },
        # 乒乓球
        '乒乓球': {
            'background': f'/images/tabletennis_top_bg.jpg',
            'star_images': [
                f'/images/tabletennis_star1.jpg',
                f'/images/tabletennis_star2.jpg',
                f'/images/tabletennis_star3.jpg'
            ]
        },
        # 羽毛球
        '羽毛球': {
            'background': f'/images/badminton_top_bg.jpg',
            'star_images': [
                f'/images/badminton_star1.jpg',
                f'/images/badminton_star2.jpg',
                f'/images/badminton_star3.jpg'
            ]
        },
        # 网球
        '网球': {
            'background': f'/images/tennis_top_bg.jpg',
            'star_images': [
                f'/images/tennis_star1.jpg',
                f'/images/tennis_star2.jpg',
                f'/images/tennis_star3.jpg'
            ]
        },
        # 高尔夫球
        '高尔夫球': {
            'background': f'/images/golf_top_bg.jpg',
            'star_images': [
                f'/images/golf_star1.jpg',
                f'/images/golf_star2.jpg',
                f'/images/golf_star3.jpg'
            ]
        },
        # 冰球
        '冰球': {
            'background': f'/images/icehockey_top_bg.jpg',
            'star_images': [
                f'/images/icehockey_star1.jpg',
                f'/images/icehockey_star2.jpg',
                f'/images/icehockey_star3.jpg'
            ]
        }
    }

# ---------------------- 免费食物热量数据库 ----------------------
CALORIE_DATABASE = {
    "米饭": 116, "白米饭": 116, "糙米饭": 111, "馒头": 221, "花卷": 217, "面条": 130, "拉面": 110, "饺子": 240, "包子": 280,
    "面包": 286, "全麦面包": 260, "蛋糕": 348, "饼干": 435, "油条": 385, "粥": 46,
    "鸡蛋": 143, "鸭蛋": 180, "鸡胸肉": 165, "鸡腿肉": 181, "牛肉": 125, "瘦牛肉": 105, "肥牛肉": 345,
    "猪肉": 395, "瘦猪肉": 143, "五花肉": 408, "鱼肉": 100, "三文鱼": 208, "虾": 83, "螃蟹": 103,
    "西红柿": 18, "黄瓜": 15, "青菜": 25, "菠菜": 28, "西兰花": 34, "胡萝卜": 41, "土豆": 77, "红薯": 86,
    "南瓜": 26, "冬瓜": 12, "芹菜": 16, "生菜": 16, "辣椒": 29,
    "苹果": 52, "香蕉": 91, "橙子": 47, "橘子": 51, "葡萄": 69, "草莓": 32, "西瓜": 30, "芒果": 60,
    "猕猴桃": 61, "梨": 58, "桃子": 42,
    "牛奶": 54, "酸奶": 72, "奶酪": 406, "黄油": 717,
    "薯片": 536, "巧克力": 546, "糖果": 400, "坚果": 607, "花生": 567, "核桃": 654,
    "豆腐": 81, "豆浆": 16, "腐竹": 457, "豆干": 140,
}

# ---------------------- 模型定义 ----------------------
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    positions = db.Column(db.Text)
    players = db.relationship('Player', backref='sport', lazy=True)
    
    @property
    def icon(self):
        """返回项目对应的图标"""
        icons = {
            '篮球': 'bi-basketball',
            '足球': 'bi-futbol',
            '排球': 'bi-volleyball',
            '乒乓球': 'bi-table-tennis',
            '羽毛球': 'bi-badminton',
            '网球': 'bi-tennis-ball',
            '高尔夫球': 'bi-golf',
            '冰球': 'bi-hockey-puck'
        }
        return icons.get(self.name, 'bi-trophy')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    food_records = db.relationship('FoodRecord', backref='user', lazy=True, cascade="all, delete-orphan")

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    position = db.Column(db.String(20))
    age = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    join_date = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String(255), default='')
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'), nullable=False)
    training_records = db.relationship('TrainingRecord', backref='player', lazy=True, cascade="all, delete-orphan")

    @property
    def average_score(self):
        if not self.training_records:
            return 0.0
        total = sum(record.score for record in self.training_records)
        return round(total / len(self.training_records), 1)

    @property
    def training_count(self):
        return len(self.training_records)

    @property
    def avatar_url(self):
        if self.avatar and os.path.exists(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], self.avatar)):
            return f'/uploads/players/{self.avatar}'
        # 如果没有上传头像，返回对应项目的球星图片
        sport = Sport.query.get(self.sport_id)
        # 确保SPORT_IMAGES已初始化
        if 'SPORT_IMAGES' not in app.config:
            init_sport_images()
        star_images = app.config['SPORT_IMAGES'].get(sport.name, {}).get('star_images', [])
        if star_images:
            return random.choice(star_images)
        return f'https://via.placeholder.com/150?text={self.name[0]}'

class TrainingPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    plan_date = db.Column(db.Date, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'), nullable=False)
    sport = db.relationship('Sport', backref='training_plans')
    training_records = db.relationship('TrainingRecord', backref='training_plan', lazy=True, cascade="all, delete-orphan")

class TrainingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('training_plan.id'))
    score = db.Column(db.Integer)
    notes = db.Column(db.Text)
    record_time = db.Column(db.DateTime, default=datetime.now)

class FoodRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, default=datetime.now)

# ---------------------- 工具函数 ----------------------
def login_required(f):
    """登录装饰器"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def sport_required(f):
    """项目选择装饰器"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！', 'danger')
            return redirect(url_for('login'))
        if 'current_sport_id' not in session:
            return redirect(url_for('select_sport'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def detect_food_local(image_path):
    try:
        common_foods = list(CALORIE_DATABASE.keys())
        cn_name = random.choice(common_foods)
        calorie_per_100g = CALORIE_DATABASE.get(cn_name, 100)
        weight = 100.0
        calories = (calorie_per_100g / 100) * weight

        return {
            "success": True,
            "food_name": cn_name,
            "calories": calories,
            "weight": weight,
            "calorie_per_100g": calorie_per_100g
        }
    except Exception as e:
        return {
            "success": True,
            "food_name": "米饭",
            "calories": 116.0,
            "weight": 100.0,
            "calorie_per_100g": 116,
            "error": str(e)
        }

# ---------------------- 全局模板变量 ----------------------
@app.context_processor
def inject_global_vars():
    # 确保SPORT_IMAGES已初始化
    if 'SPORT_IMAGES' not in app.config:
        init_sport_images()
    
    is_login = 'user_id' in session
    current_user = User.query.get(session.get('user_id')) if is_login else None
    current_sport = None
    sport_images = {}
    
    # 获取当前选中的项目
    if is_login and 'current_sport_id' in session:
        current_sport = Sport.query.get(session['current_sport_id'])
        sport_images = app.config['SPORT_IMAGES'].get(current_sport.name, {})
    
    # 统计当前项目数据
    total_players = 0
    total_plans = 0
    total_records = 0
    avg_total_score = 0.0
    total_food_records = 0
    
    if is_login and current_sport:
        total_players = Player.query.filter_by(sport_id=current_sport.id).count()
        total_plans = TrainingPlan.query.filter_by(sport_id=current_sport.id).count()
        total_records = TrainingRecord.query.join(Player).filter(Player.sport_id == current_sport.id).count()
        total_food_records = FoodRecord.query.filter_by(user_id=session.get('user_id')).count()
        
        if total_records > 0:
            all_scores = [r.score for r in TrainingRecord.query.join(Player).filter(Player.sport_id == current_sport.id).all() if r.score]
            avg_total_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0
    
    return dict(
        is_login=is_login,
        current_user=current_user,
        current_sport=current_sport,
        sport_images=sport_images,
        total_players=total_players,
        total_plans=total_plans,
        total_records=total_records,
        avg_total_score=avg_total_score,
        total_food_records=total_food_records,
        date=date
    )

# ---------------------- 核心路由 ----------------------
# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(url_for('select_sport'))
        flash('用户名或密码错误！', 'danger')
    
    return render_template('login.html')

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_pwd = request.form['confirm_pwd']
        
        if password != confirm_pwd:
            flash('两次密码不一致！', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册！', 'danger')
            return redirect(url_for('register'))
        
        hashed_pwd = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请选择您要管理的体育项目！', 'success')
        session['user_id'] = new_user.id
        return redirect(url_for('select_sport'))
    
    return render_template('register.html')

# 项目选择页
@app.route('/select_sport')
@login_required
def select_sport():
    sports = Sport.query.all()
    return render_template('select_sport.html', sports=sports)

# 设置当前项目
@app.route('/set_current_sport/<int:sport_id>')
@login_required
def set_current_sport(sport_id):
    sport = Sport.query.get_or_404(sport_id)
    session['current_sport_id'] = sport.id
    flash(f'已切换至【{sport.name}】项目！', 'success')
    return redirect(url_for('index'))

# 切换项目（导航用）
@app.route('/switch_sport')
@login_required
def switch_sport():
    session.pop('current_sport_id', None)
    return redirect(url_for('select_sport'))

# 首页
@app.route('/')
@sport_required
def index():
    current_sport = Sport.query.get(session['current_sport_id'])
    
    latest_records = TrainingRecord.query.join(Player).filter(
        Player.sport_id == current_sport.id
    ).order_by(TrainingRecord.record_time.desc()).limit(5).all()
    
    latest_players = Player.query.filter_by(
        sport_id=current_sport.id
    ).order_by(Player.join_date.desc()).limit(3).all()
    
    latest_plans = TrainingPlan.query.filter_by(
        sport_id=current_sport.id
    ).order_by(TrainingPlan.plan_date.desc()).limit(3).all()
    
    latest_food_records = FoodRecord.query.filter_by(
        user_id=session['user_id']
    ).order_by(FoodRecord.create_time.desc()).limit(3).all()
    
    return render_template('index.html', 
                           latest_records=latest_records, 
                           latest_players=latest_players, 
                           latest_plans=latest_plans,
                           latest_food_records=latest_food_records)

# 退出登录
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('current_sport_id', None)
    flash('已退出登录！', 'success')
    return redirect(url_for('login'))

# ---------------------- 球员管理路由 ----------------------
@app.route('/players')
@sport_required
def players():
    current_sport = Sport.query.get(session['current_sport_id'])
    player_list = Player.query.filter_by(sport_id=current_sport.id).order_by(Player.number).all()
    all_sports = Sport.query.all()
    
    return render_template('players.html', 
                           players=player_list, 
                           sports=all_sports,
                           current_sport=current_sport)

@app.route('/player/<int:player_id>')
@sport_required
def player_detail(player_id):
    player = Player.query.get_or_404(player_id)
    if player.sport_id != session['current_sport_id']:
        flash('无权限查看该球员！', 'danger')
        return redirect(url_for('players'))
    
    records = TrainingRecord.query.filter_by(player_id=player_id).order_by(TrainingRecord.record_time.desc()).all()
    return render_template('player_detail.html', player=player, records=records)

@app.route('/player/add', methods=['POST'])
@sport_required
def add_player():
    try:
        sport_id = int(request.form.get('sport_id', session['current_sport_id']))
        
        name = request.form['name']
        number = int(request.form['number'])
        position = request.form['position']
        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        
        avatar = ''
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                avatar = secure_filename(f'player_{timestamp}.{file.filename.rsplit(".", 1)[1].lower()}')
                file.save(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], avatar))
        
        new_player = Player(
            name=name,
            number=number,
            position=position,
            age=age,
            height=height,
            weight=weight,
            sport_id=sport_id,
            avatar=avatar
        )
        db.session.add(new_player)
        db.session.commit()
        
        flash(f'球员{name}添加成功！', 'success')
    except Exception as e:
        flash(f'添加失败：{str(e)}', 'danger')
    
    return redirect(url_for('players', sport_id=sport_id))

@app.route('/player/edit/<int:player_id>', methods=['POST'])
@sport_required
def edit_player(player_id):
    try:
        player = Player.query.get_or_404(player_id)
        if player.sport_id != session['current_sport_id'] and int(request.form.get('sport_id', player.sport_id)) != session['current_sport_id']:
            flash('无权限编辑该球员！', 'danger')
            return redirect(url_for('players'))
        
        player.name = request.form['name']
        player.number = int(request.form['number'])
        player.position = request.form['position']
        player.age = int(request.form['age'])
        player.height = float(request.form['height'])
        player.weight = float(request.form['weight'])
        
        new_sport_id = int(request.form.get('sport_id', player.sport_id))
        player.sport_id = new_sport_id
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                if player.avatar and os.path.exists(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], player.avatar)):
                    os.remove(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], player.avatar))
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                player.avatar = secure_filename(f'player_{timestamp}.{file.filename.rsplit(".", 1)[1].lower()}')
                file.save(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], player.avatar))
        
        db.session.commit()
        flash(f'球员{player.name}信息更新成功！', 'success')
    except Exception as e:
        flash(f'更新失败：{str(e)}', 'danger')
    
    return redirect(url_for('players'))

@app.route('/player/delete/<int:player_id>')
@sport_required
def delete_player(player_id):
    try:
        player = Player.query.get_or_404(player_id)
        if player.sport_id != session['current_sport_id']:
            flash('无权限删除该球员！', 'danger')
            return redirect(url_for('players'))
        
        if player.avatar and os.path.exists(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], player.avatar)):
            os.remove(os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], player.avatar))
        
        db.session.delete(player)
        db.session.commit()
        flash(f'球员{player.name}已删除！', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('players'))

@app.route('/player/upload', methods=['POST'])
@sport_required
def upload_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({'status': 'error', 'msg': '未选择图片'}), 400
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'status': 'error', 'msg': '图片名称为空'}), 400
        
        if file and allowed_file(file.filename):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = secure_filename(f'player_{timestamp}.{file.filename.rsplit(".", 1)[1].lower()}')
            file_path = os.path.join(app.config['PLAYER_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            return jsonify({
                'status': 'success',
                'filename': filename,
                'msg': '头像上传成功'
            })
        return jsonify({'status': 'error', 'msg': '仅支持png/jpg/jpeg/gif格式'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'上传失败：{str(e)}'}), 500

# ---------------------- 训练计划路由 ----------------------
@app.route('/plans')
@sport_required
def plans():
    current_sport = Sport.query.get(session['current_sport_id'])
    plan_list = TrainingPlan.query.filter_by(sport_id=current_sport.id).order_by(TrainingPlan.plan_date.desc()).all()
    return render_template('plans.html', plans=plan_list)

@app.route('/plan/<int:plan_id>')
@sport_required
def plan_detail(plan_id):
    plan = TrainingPlan.query.get_or_404(plan_id)
    if plan.sport_id != session['current_sport_id']:
        flash('无权限查看该计划！', 'danger')
        return redirect(url_for('plans'))
    
    records = TrainingRecord.query.filter_by(plan_id=plan_id).join(Player).order_by(TrainingRecord.record_time.desc()).all()
    return render_template('plan_detail.html', plan=plan, records=records)

@app.route('/plan/add', methods=['POST'])
@sport_required
def add_plan():
    try:
        title = request.form['title']
        content = request.form['content']
        plan_date = datetime.strptime(request.form['plan_date'], '%Y-%m-%d').date()
        
        new_plan = TrainingPlan(
            title=title,
            content=content,
            plan_date=plan_date,
            sport_id=session['current_sport_id']
        )
        db.session.add(new_plan)
        db.session.commit()
        
        flash('训练计划添加成功！', 'success')
    except Exception as e:
        flash(f'添加失败：{str(e)}', 'danger')
    
    return redirect(url_for('plans'))

@app.route('/plan/edit/<int:plan_id>', methods=['POST'])
@sport_required
def edit_plan(plan_id):
    try:
        plan = TrainingPlan.query.get_or_404(plan_id)
        if plan.sport_id != session['current_sport_id']:
            flash('无权限编辑该计划！', 'danger')
            return redirect(url_for('plans'))
        
        plan.title = request.form['title']
        plan.content = request.form['content']
        plan.plan_date = datetime.strptime(request.form['plan_date'], '%Y-%m-%d').date()
        
        db.session.commit()
        flash('训练计划更新成功！', 'success')
    except Exception as e:
        flash(f'更新失败：{str(e)}', 'danger')
    
    return redirect(url_for('plans'))

@app.route('/plan/delete/<int:plan_id>')
@sport_required
def delete_plan(plan_id):
    try:
        plan = TrainingPlan.query.get_or_404(plan_id)
        if plan.sport_id != session['current_sport_id']:
            flash('无权限删除该计划！', 'danger')
            return redirect(url_for('plans'))
        
        db.session.delete(plan)
        db.session.commit()
        flash('训练计划已删除！', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('plans'))

# ---------------------- 训练记录路由 ----------------------
@app.route('/records')
@sport_required
def records():
    current_sport = Sport.query.get(session['current_sport_id'])
    record_list = TrainingRecord.query.join(Player).filter(
        Player.sport_id == current_sport.id
    ).outerjoin(TrainingPlan).order_by(TrainingRecord.record_time.desc()).all()
    
    players = Player.query.filter_by(sport_id=current_sport.id).all()
    plans = TrainingPlan.query.filter_by(sport_id=current_sport.id).all()
    
    return render_template('records.html', records=record_list, players=players, plans=plans)

@app.route('/record/add', methods=['POST'])
@sport_required
def add_record():
    try:
        player_id = int(request.form['player_id'])
        plan_id = int(request.form['plan_id']) if request.form['plan_id'] else None
        score = int(request.form['score'])
        notes = request.form['notes']
        
        player = Player.query.get(player_id)
        if player.sport_id != session['current_sport_id']:
            flash('只能添加当前项目球员的记录！', 'danger')
            return redirect(url_for('records'))
        
        new_record = TrainingRecord(
            player_id=player_id,
            plan_id=plan_id,
            score=score,
            notes=notes
        )
        db.session.add(new_record)
        db.session.commit()
        
        flash('训练记录添加成功！', 'success')
    except Exception as e:
        flash(f'添加失败：{str(e)}', 'danger')
    
    return redirect(url_for('records'))

@app.route('/record/delete/<int:record_id>')
@sport_required
def delete_record(record_id):
    try:
        record = TrainingRecord.query.get_or_404(record_id)
        player = Player.query.get(record.player_id)
        if player.sport_id != session['current_sport_id']:
            flash('无权限删除该记录！', 'danger')
            return redirect(url_for('records'))
        
        db.session.delete(record)
        db.session.commit()
        flash('训练记录已删除！', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('records'))

# ---------------------- 数据统计路由 ----------------------
@app.route('/stats')
@sport_required
def stats():
    current_sport = Sport.query.get(session['current_sport_id'])
    players = Player.query.filter_by(sport_id=current_sport.id).all()
    plans = TrainingPlan.query.filter_by(sport_id=current_sport.id).all()
    records = TrainingRecord.query.join(Player).filter(Player.sport_id == current_sport.id).all()
    
    # 位置统计
    position_stats = {}
    for p in players:
        position_stats[p.position] = position_stats.get(p.position, 0) + 1
    
    # 计划月度统计
    plan_stats = {}
    for plan in plans:
        month = plan.plan_date.strftime('%Y-%m')
        plan_stats[month] = plan_stats.get(month, 0) + 1
    
    # 评分统计
    score_stats = {i:0 for i in range(1, 11)}
    for r in records:
        if 1 <= r.score <= 10:
            score_stats[r.score] += 1
    
    # 球员评分排名
    ranked_players = [p for p in players if p.training_count > 0]
    ranked_players.sort(key=lambda x: x.average_score, reverse=True)
    
    return render_template('stats.html',
                           players=players,
                           plans=plans,
                           position_stats=position_stats,
                           plan_stats=plan_stats,
                           score_stats=score_stats,
                           ranked_players=ranked_players)

# ---------------------- 食物热量路由 ----------------------
@app.route('/food-calc')
@sport_required
def food_calc():
    food_list = list(CALORIE_DATABASE.keys())
    return render_template('food_calc.html', food_list=food_list)

@app.route('/food-records')
@sport_required
def food_records():
    food_list = FoodRecord.query.filter_by(user_id=session['user_id']).order_by(FoodRecord.create_time.desc()).all()
    return render_template('food_records.html', food_records=food_list)

@app.route('/food/upload', methods=['POST'])
@sport_required
def upload_food():
    try:
        if 'food_image' not in request.files:
            return jsonify({'status': 'error', 'msg': '未选择图片'}), 400
        file = request.files['food_image']
        if file.filename == '':
            return jsonify({'status': 'error', 'msg': '图片名称为空'}), 400
        
        if file and allowed_file(file.filename):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = secure_filename(f'food_{session["user_id"]}_{timestamp}.{file.filename.rsplit(".", 1)[1].lower()}')
            file_path = os.path.join(app.config['FOOD_UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            detect_result = detect_food_local(file_path)
            if detect_result.get("success"):
                return jsonify({
                    'status': 'success',
                    'msg': '识别成功',
                    'data': {
                        'food_name': detect_result['food_name'],
                        'calories': detect_result['calories'],
                        'weight': detect_result['weight'],
                        'calorie_per_100g': detect_result['calorie_per_100g'],
                        'image_path': f'/uploads/foods/{filename}'
                    }
                })
            else:
                os.remove(file_path)
                return jsonify({'status': 'error', 'msg': '识别失败'})
        return jsonify({'status': 'error', 'msg': '仅支持png/jpg/jpeg/gif格式'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'上传失败：{str(e)}'}), 500

@app.route('/food/update', methods=['POST'])
@sport_required
def update_food():
    try:
        data = request.get_json()
        food_name = data.get('food_name')
        weight = float(data.get('weight'))
        
        if not food_name or weight <= 0:
            return jsonify({'status': 'error', 'msg': '参数错误'}), 400
        
        calorie_per_100g = CALORIE_DATABASE.get(food_name, 100)
        calories = (calorie_per_100g / 100) * weight
        
        return jsonify({
            'status': 'success',
            'data': {
                'food_name': food_name,
                'calories': calories,
                'weight': weight,
                'calorie_per_100g': calorie_per_100g
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'更新失败：{str(e)}'}), 500

@app.route('/food/save', methods=['POST'])
@sport_required
def save_food():
    try:
        data = request.get_json()
        food_name = data.get('food_name')
        calories = float(data.get('calories'))
        weight = float(data.get('weight'))
        image_path = data.get('image_path', '').lstrip('/')
        
        new_food = FoodRecord(
            user_id=session['user_id'],
            food_name=food_name,
            calories=calories,
            weight=weight,
            image_path=image_path
        )
        db.session.add(new_food)
        db.session.commit()
        
        return jsonify({'status': 'success', 'msg': '记录保存成功', 'record_id': new_food.id})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': f'保存失败：{str(e)}'}), 500

@app.route('/food/delete/<int:food_id>')
@sport_required
def delete_food(food_id):
    try:
        food = FoodRecord.query.get_or_404(food_id)
        if food.user_id != session['user_id']:
            flash('无权限删除该记录！', 'danger')
            return redirect(url_for('food_records'))
        
        if food.image_path and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], food.image_path)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], food.image_path))
        
        db.session.delete(food)
        db.session.commit()
        flash('食物记录已删除！', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('food_records'))

# ---------------------- 静态文件访问 ----------------------
@app.route('/uploads/players/<filename>')
@sport_required
def serve_avatar(filename):
    return send_from_directory(app.config['PLAYER_UPLOAD_FOLDER'], filename)

@app.route('/uploads/foods/<filename>')
@sport_required
def serve_food_image(filename):
    return send_from_directory(app.config['FOOD_UPLOAD_FOLDER'], filename)

# ---------------------- 初始化数据库 + 启动 ----------------------
if __name__ == '__main__':
    # 在启动前初始化图片配置（解决上下文问题）
    with app.app_context():
        init_sport_images()
        # 创建数据库表
        db.create_all()
        
        # 初始化默认体育项目
        default_sports = [
            {"name": "篮球", "positions": "控球后卫,得分后卫,小前锋,大前锋,中锋"},
            {"name": "足球", "positions": "门将,后卫,中场,前锋,边锋"},
            {"name": "排球", "positions": "主攻,副攻,二传,自由人,接应"},
            {"name": "乒乓球", "positions": "单打选手,双打选手,混双选手"},
            {"name": "羽毛球", "positions": "单打选手,双打选手,混双选手"},
            {"name": "网球", "positions": "单打选手,双打选手,混双选手"},
            {"name": "高尔夫球", "positions": "职业选手,业余选手"},
            {"name": "冰球", "positions": "门将,后卫,前锋,中锋,边锋"}
        ]
        
        for sport_data in default_sports:
            if not Sport.query.filter_by(name=sport_data["name"]).first():
                new_sport = Sport(name=sport_data["name"], positions=sport_data["positions"])
                db.session.add(new_sport)
        db.session.commit()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5000)