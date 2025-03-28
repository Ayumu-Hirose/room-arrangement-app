import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io
import base64

# アプリのタイトルとデザイン設定
st.set_page_config(page_title="模様替えシミュレーター", layout="wide")

# CSSでアプリのスタイルを設定
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stSelectbox label, .stSlider label {
        font-weight: bold;
        color: #333;
    }
    h1, h2, h3 {
        color: #2E7D32;
    }
</style>
""", unsafe_allow_html=True)

# アプリのタイトル
st.title("部屋の模様替えシミュレーター")
st.write("このアプリでは、部屋のレイアウトや色をシミュレーションできます。")

# サイドバーの設定
st.sidebar.header("設定パネル")

# 部屋の設定
st.sidebar.subheader("部屋の設定")
room_width = st.sidebar.slider("部屋の幅 (m)", 3.0, 10.0, 6.0, 0.1)
room_length = st.sidebar.slider("部屋の奥行き (m)", 3.0, 10.0, 8.0, 0.1)
wall_color = st.sidebar.color_picker("壁の色", "#FFFFFF")
floor_color = st.sidebar.color_picker("床の色", "#8B4513")

# 家具の設定
st.sidebar.subheader("家具の追加")
furniture_type = st.sidebar.selectbox(
    "家具の種類",
    ["ベッド", "テーブル", "椅子", "ソファ", "本棚", "テレビ"]
)

# 家具のサイズ設定
if furniture_type == "ベッド":
    furniture_width = st.sidebar.slider("幅 (m)", 0.8, 2.0, 1.4, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 1.8, 2.2, 2.0, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#87CEEB")
elif furniture_type == "テーブル":
    furniture_width = st.sidebar.slider("幅 (m)", 0.6, 2.0, 1.2, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 0.6, 2.0, 1.6, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#8B4513")
elif furniture_type == "椅子":
    furniture_width = st.sidebar.slider("幅 (m)", 0.4, 0.8, 0.5, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 0.4, 0.8, 0.5, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#A0522D")
elif furniture_type == "ソファ":
    furniture_width = st.sidebar.slider("幅 (m)", 0.8, 3.0, 2.0, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 0.8, 1.5, 1.0, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#708090")
elif furniture_type == "本棚":
    furniture_width = st.sidebar.slider("幅 (m)", 0.3, 2.0, 1.0, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 0.3, 0.6, 0.4, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#8B4513")
else:  # テレビ
    furniture_width = st.sidebar.slider("幅 (m)", 0.8, 2.0, 1.2, 0.1)
    furniture_length = st.sidebar.slider("長さ (m)", 0.1, 0.3, 0.2, 0.1)
    furniture_color = st.sidebar.color_picker("色", "#000000")

# 位置設定
furniture_x = st.sidebar.slider("X位置 (左から)", 0.1, room_width - 0.1, room_width / 2, 0.1)
furniture_y = st.sidebar.slider("Y位置 (上から)", 0.1, room_length - 0.1, room_length / 2, 0.1)
furniture_rotation = st.sidebar.slider("回転 (度)", 0, 359, 0, 15)

# 家具リスト（セッション状態を使用）
if 'furniture_list' not in st.session_state:
    st.session_state.furniture_list = []

# 家具を追加するボタン
if st.sidebar.button("家具を追加"):
    new_furniture = {
        "type": furniture_type,
        "width": furniture_width,
        "length": furniture_length,
        "color": furniture_color,
        "x": furniture_x,
        "y": furniture_y,
        "rotation": furniture_rotation
    }
    st.session_state.furniture_list.append(new_furniture)
    st.sidebar.success(f"{furniture_type}を追加しました！")

# 家具リストを表示
st.sidebar.subheader("配置済みの家具")
for i, furniture in enumerate(st.session_state.furniture_list):
    with st.sidebar.expander(f"{furniture['type']} {i+1}"):
        st.write(f"幅: {furniture['width']}m, 長さ: {furniture['length']}m")
        st.write(f"位置: X={furniture['x']}m, Y={furniture['y']}m")
        st.write(f"回転: {furniture['rotation']}度")
        if st.button("削除", key=f"delete_{i}"):
            st.session_state.furniture_list.pop(i)
            st.experimental_rerun()

# リセットボタン
if st.sidebar.button("すべてリセット"):
    st.session_state.furniture_list = []
    st.experimental_rerun()

# 表示設定
scale_factor = 50  # 1mあたりのピクセル数

# 部屋のレンダリング関数
def render_room():
    # 部屋のサイズを計算（ピクセル単位）
    width_px = int(room_width * scale_factor)
    length_px = int(room_length * scale_factor)
    
    # 新しい画像を作成
    room_image = Image.new('RGB', (width_px, length_px), color=wall_color)
    draw = ImageDraw.Draw(room_image)
    
    # 床を描画
    draw.rectangle([0, 0, width_px, length_px], fill=floor_color)
    
    # 家具を描画
    for furniture in st.session_state.furniture_list:
        # 家具のサイズと位置を計算
        f_width_px = int(furniture["width"] * scale_factor)
        f_length_px = int(furniture["length"] * scale_factor)
        f_x_px = int(furniture["x"] * scale_factor - f_width_px/2)
        f_y_px = int(furniture["y"] * scale_factor - f_length_px/2)
        
        # 回転を適用（簡易版 - 回転なしで四角形を描画）
        if furniture["rotation"] == 0:
            draw.rectangle(
                [f_x_px, f_y_px, f_x_px + f_width_px, f_y_px + f_length_px],
                fill=furniture["color"],
                outline="#000000"
            )
        else:
            # 家具の中心を計算
            center_x = f_x_px + f_width_px/2
            center_y = f_y_px + f_length_px/2
            
            # 回転を計算（簡易版）
            angle_rad = np.radians(furniture["rotation"])
            cos_theta = np.cos(angle_rad)
            sin_theta = np.sin(angle_rad)
            
            # 回転した四角形の頂点を計算
            half_width = f_width_px / 2
            half_length = f_length_px / 2
            
            # 四つの頂点
            points = [
                (-half_width, -half_length),  # 左上
                (half_width, -half_length),   # 右上
                (half_width, half_length),    # 右下
                (-half_width, half_length)    # 左下
            ]
            
            # 回転を適用して中心に移動
            rotated_points = []
            for px, py in points:
                rx = px * cos_theta - py * sin_theta + center_x
                ry = px * sin_theta + py * cos_theta + center_y
                rotated_points.append((rx, ry))
            
            # 多角形を描画
            draw.polygon(rotated_points, fill=furniture["color"], outline="#000000")

        # 家具の種類を表示するテキスト
        # （シンプルにするため、回転は考慮していません）
        draw.text((f_x_px + f_width_px/2 - 10, f_y_px + f_length_px/2 - 5), 
                 furniture["type"][:1], fill="#FFFFFF")
    
    return room_image

# 部屋を描画
room_image = render_room()

# 画像をストリーミングするための関数
def get_image_download_link(img, filename, text):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

# メインエリアに部屋の図を表示
st.subheader("部屋のレイアウト")
st.image(room_image, use_column_width=True)

# 画像のダウンロードリンク
st.markdown(
    get_image_download_link(room_image, "room_layout.png", "部屋のレイアウトをダウンロード"),
    unsafe_allow_html=True
)

# 使い方とヒントを表示
with st.expander("使い方とヒント"):
    st.write("""
    1. サイドバーで部屋のサイズと色を設定します。
    2. 追加したい家具を選択し、サイズ、色、位置を調整します。
    3. 「家具を追加」ボタンをクリックして部屋に配置します。
    4. 配置済みの家具は、サイドバーのリストから確認・削除できます。
    5. レイアウトが完成したら、画像をダウンロードできます。
    
    **ヒント:**
    - 家具は重ねて配置できますが、後から追加した家具が上に表示されます。
    - 詳細なレイアウトを作成するには、小さな家具を組み合わせると効果的です。
    - 壁と床の色を変えることで、部屋の雰囲気を変えることができます。
    """)

# アプリのフッター
st.markdown("---")
st.markdown("© 2025 模様替えシミュレーター | Powered by Streamlit")
