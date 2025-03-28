import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import pandas as pd
import json
import os
from datetime import datetime

# アプリのタイトルとデザイン設定
st.set_page_config(page_title="工場レイアウトシミュレーター", layout="wide")

# CSSでアプリのスタイルを設定
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton button {
        background-color: #0277BD;
        color: white;
        font-weight: bold;
    }
    .stSelectbox label, .stSlider label {
        font-weight: bold;
        color: #333;
    }
    h1, h2, h3 {
        color: #1565C0;
    }
    .equipment-list {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .stats-container {
        background-color: #E3F2FD;
        border-radius: 5px;
        padding: 10px;
        margin-top: 15px;
    }
    .footer {
        margin-top: 50px;
        text-align: center;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'equipment_list' not in st.session_state:
    st.session_state.equipment_list = []
if 'current_layout_name' not in st.session_state:
    st.session_state.current_layout_name = "新規レイアウト"
if 'layouts' not in st.session_state:
    st.session_state.layouts = {}
if 'show_grid' not in st.session_state:
    st.session_state.show_grid = True
if 'show_collision' not in st.session_state:
    st.session_state.show_collision = True
if 'show_equipment_info' not in st.session_state:
    st.session_state.show_equipment_info = True

# アプリのタイトル
st.title("工場レイアウトシミュレーター")
st.write("工場内の設備配置をシミュレーションできるツールです。設備の追加・位置調整・保存が可能です。")

# メインコンテンツとサイドバーのレイアウト
col1, col2 = st.columns([2, 1])

# サイドバー（設定パネル）
with col2:
    st.header("設定パネル")
    
    # レイアウトの保存と読み込み
    with st.expander("レイアウトの保存/読み込み", expanded=True):
        layout_name = st.text_input("レイアウト名", st.session_state.current_layout_name)
        
        col_save, col_load = st.columns(2)
        with col_save:
            if st.button("レイアウトを保存"):
                if layout_name:
                    # 現在の設定とレイアウトを保存
                    st.session_state.layouts[layout_name] = {
                        "equipment_list": st.session_state.equipment_list.copy(),
                        "factory_width": st.session_state.factory_width,
                        "factory_length": st.session_state.factory_length,
                        "floor_color": st.session_state.floor_color,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    st.session_state.current_layout_name = layout_name
                    st.success(f"レイアウト '{layout_name}' を保存しました")
        
        with col_load:
            if st.session_state.layouts:
                layout_options = list(st.session_state.layouts.keys())
                selected_layout = st.selectbox("保存済みレイアウト", layout_options)
                
                if st.button("読み込む"):
                    # 選択したレイアウトを読み込む
                    layout_data = st.session_state.layouts[selected_layout]
                    st.session_state.equipment_list = layout_data["equipment_list"].copy()
                    st.session_state.factory_width = layout_data["factory_width"]
                    st.session_state.factory_length = layout_data["factory_length"]
                    st.session_state.floor_color = layout_data["floor_color"]
                    st.session_state.current_layout_name = selected_layout
                    st.success(f"レイアウト '{selected_layout}' を読み込みました")
            else:
                st.info("保存済みレイアウトはありません")
        
        # JSONでエクスポート/インポート
        if st.button("JSONでエクスポート"):
            export_data = {
                "layout_name": st.session_state.current_layout_name,
                "equipment_list": st.session_state.equipment_list,
                "factory_width": st.session_state.factory_width,
                "factory_length": st.session_state.factory_length,
                "floor_color": st.session_state.floor_color
            }
            json_str = json.dumps(export_data, indent=2)
            b64 = base64.b64encode(json_str.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="{layout_name.replace(" ", "_")}_layout.json">JSONファイルをダウンロード</a>'
            st.markdown(href, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("JSONファイルをインポート", type=["json"])
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                st.session_state.equipment_list = import_data["equipment_list"]
                st.session_state.factory_width = import_data["factory_width"]
                st.session_state.factory_length = import_data["factory_length"]
                st.session_state.floor_color = import_data["floor_color"]
                st.session_state.current_layout_name = import_data["layout_name"]
                st.success("レイアウトを正常にインポートしました")
            except Exception as e:
                st.error(f"インポート中にエラーが発生しました: {e}")

    # 工場エリアの設定
    with st.expander("工場エリアの設定", expanded=True):
        # 初期値の設定（セッション状態がない場合）
        if 'factory_width' not in st.session_state:
            st.session_state.factory_width = 20.0
        if 'factory_length' not in st.session_state:
            st.session_state.factory_length = 25.0
        if 'floor_color' not in st.session_state:
            st.session_state.floor_color = "#CCCCCC"
        
        # 工場サイズの設定スライダー
        factory_width = st.slider("工場の幅 (m)", 5.0, 30.0, st.session_state.factory_width, 1.0)
        factory_length = st.slider("工場の奥行き (m)", 5.0, 30.0, st.session_state.factory_length, 1.0)
        
        # 色の設定
        floor_color = st.color_picker("床の色", st.session_state.floor_color)
        
        # セッション状態を更新
        st.session_state.factory_width = factory_width
        st.session_state.factory_length = factory_length
        st.session_state.floor_color = floor_color
        
        # 表示オプション
        st.checkbox("グリッド表示", value=st.session_state.show_grid, key="show_grid")
        st.checkbox("衝突検出表示", value=st.session_state.show_collision, key="show_collision")
        st.checkbox("設備情報表示", value=st.session_state.show_equipment_info, key="show_equipment_info")

    # 設備の追加設定
    with st.expander("設備の追加", expanded=True):
        # 設備種類のデフォルトサイズマップ
        equipment_defaults = {
            "robot": {"width": 2.0, "length": 2.0, "color": "#FF9800", "label": "産業用ロボット"},
            "machine": {"width": 3.0, "length": 5.0, "color": "#2196F3", "label": "加工機械"},
            "conveyor": {"width": 1.0, "length": 10.0, "color": "#8BC34A", "label": "コンベヤー"},
            "workstation": {"width": 2.0, "length": 3.0, "color": "#9C27B0", "label": "作業台"},
            "storage": {"width": 5.0, "length": 8.0, "color": "#795548", "label": "倉庫/棚"},
            "agv": {"width": 1.5, "length": 2.5, "color": "#FFEB3B", "label": "AGV/無人搬送車"},
            "custom": {"width": 4.0, "length": 4.0, "color": "#607D8B", "label": "カスタム設備"}
        }
        
        # 設備の種類選択
        equipment_type = st.selectbox(
            "設備の種類",
            list(equipment_defaults.keys()),
            format_func=lambda x: equipment_defaults[x]["label"]
        )
        
        # 選択された設備のデフォルト値
        defaults = equipment_defaults[equipment_type]
        
        # 設備のサイズと色の設定
        equipment_width = st.slider("幅 (m)", 0.5, 20.0, defaults["width"], 0.5)
        equipment_length = st.slider("長さ (m)", 0.5, 20.0, defaults["length"], 0.5)
        equipment_color = st.color_picker("色", defaults["color"])
        
        # 回転角度
        equipment_rotation = st.slider("回転 (度)", 0, 359, 0, 15)
        
        # 設備ラベル
        equipment_label = st.text_input("設備名/ラベル", defaults["label"])
        
        # 設備の位置指定
        st.subheader("配置位置")
        col_x, col_y = st.columns(2)
        with col_x:
            equipment_x = st.number_input("X位置 (m)", 0.0, factory_width, factory_width / 2, 0.5)
        with col_y:
            equipment_y = st.number_input("Y位置 (m)", 0.0, factory_length, factory_length / 2, 0.5)
        
        # 設備の追加ボタン
        if st.button("設備を追加"):
            new_equipment = {
                "type": equipment_type,
                "width": equipment_width,
                "length": equipment_length,
                "color": equipment_color,
                "x": equipment_x,
                "y": equipment_y,
                "rotation": equipment_rotation,
                "label": equipment_label,
                "id": len(st.session_state.equipment_list)
            }
            
            st.session_state.equipment_list.append(new_equipment)
            st.success(f"{equipment_label}を追加しました！")
            # アニメーション効果を追加
            st.balloons()

    # 統計情報
    with st.expander("統計情報", expanded=True):
        if st.session_state.equipment_list:
            total_area = sum(item["width"] * item["length"] for item in st.session_state.equipment_list)
            factory_area = factory_width * factory_length
            area_usage = (total_area / factory_area) * 100
            
            st.markdown('<div class="stats-container">', unsafe_allow_html=True)
            st.write(f"**設備の数:** {len(st.session_state.equipment_list)}")
            st.write(f"**総設備面積:** {total_area:.1f} m²")
            st.write(f"**工場総面積:** {factory_area:.1f} m²")
            st.write(f"**面積使用率:** {area_usage:.1f}%")
            
            # 設備タイプごとの統計
            equipment_counts = {}
            for item in st.session_state.equipment_list:
                equipment_type = item["type"]
                label = equipment_defaults[equipment_type]["label"]
                if label in equipment_counts:
                    equipment_counts[label] += 1
                else:
                    equipment_counts[label] = 1
            
            if equipment_counts:
                st.write("**設備タイプ別の数:**")
                for label, count in equipment_counts.items():
                    st.write(f"- {label}: {count}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# メイン表示エリア（レイアウト図）
with col1:
    # 表示するレイアウトのサイズ計算と描画関数
    scale_factor = 20  # 1mあたりのピクセル数
    
    # 設備の衝突検出関数
    def detect_collisions(equipment_list):
        collisions = []
        for i, equip1 in enumerate(equipment_list):
            for j, equip2 in enumerate(equipment_list[i+1:], i+1):
                # 簡易的な衝突チェック（回転を考慮していない）
                # より複雑なレイアウトでは回転を考慮した衝突検出が必要
                x1_min = equip1["x"] - equip1["width"]/2
                x1_max = equip1["x"] + equip1["width"]/2
                y1_min = equip1["y"] - equip1["length"]/2
                y1_max = equip1["y"] + equip1["length"]/2
                
                x2_min = equip2["x"] - equip2["width"]/2
                x2_max = equip2["x"] + equip2["width"]/2
                y2_min = equip2["y"] - equip2["length"]/2
                y2_max = equip2["y"] + equip2["length"]/2
                
                # 重なりがあれば衝突
                if (x1_min < x2_max and x1_max > x2_min and
                    y1_min < y2_max and y1_max > y2_min):
                    collisions.append((i, j))
        return collisions
    
    # レイアウト図を描画する関数
    def render_layout():
        # 工場エリアのサイズを計算（ピクセル単位）
        width_px = int(st.session_state.factory_width * scale_factor)
        length_px = int(st.session_state.factory_length * scale_factor)
        
        # 新しい画像を作成
        factory_image = Image.new('RGB', (width_px, length_px), color="#FFFFFF")
        draw = ImageDraw.Draw(factory_image)
        
        # 床を描画
        draw.rectangle([0, 0, width_px, length_px], fill=st.session_state.floor_color)
        
        # グリッドを描画（オプション）
        if st.session_state.show_grid:
            grid_color = "#AAAAAA"
            # 縦線
            for x in range(0, width_px + 1, scale_factor):
                draw.line([(x, 0), (x, length_px)], fill=grid_color, width=1)
            # 横線
            for y in range(0, length_px + 1, scale_factor):
                draw.line([(0, y), (width_px, y)], fill=grid_color, width=1)
        
        # 衝突検出
        collisions = []
        if st.session_state.show_collision:
            collisions = detect_collisions(st.session_state.equipment_list)
        
        # フォントの設定
        try:
            font = ImageFont.truetype("arial.ttf", 12)
            big_font = ImageFont.truetype("arial.ttf", 16)
        except IOError:
            # フォントが見つからない場合はデフォルトフォントを使用
            font = ImageFont.load_default()
            big_font = ImageFont.load_default()
        
        # 設備を描画
        for i, equipment in enumerate(st.session_state.equipment_list):
            # 設備のサイズと位置を計算
            width_eq = int(equipment["width"] * scale_factor)
            length_eq = int(equipment["length"] * scale_factor)
            x_eq = int(equipment["x"] * scale_factor)
            y_eq = int(equipment["y"] * scale_factor)
            
            # 衝突している設備かどうかをチェック
            is_collision = any(i in collision for collision in collisions)
            
            # 回転を考慮した描画
            angle_rad = np.radians(equipment["rotation"])
            cos_theta = np.cos(angle_rad)
            sin_theta = np.sin(angle_rad)
            
            # 回転した四角形の頂点を計算
            half_width = width_eq / 2
            half_length = length_eq / 2
            
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
                rx = px * cos_theta - py * sin_theta + x_eq
                ry = px * sin_theta + py * cos_theta + y_eq
                rotated_points.append((rx, ry))
            
            # 多角形を描画（衝突していれば赤い縁取り）
            fill_color = equipment["color"]
            outline_color = "#FF0000" if is_collision else "#000000"
            outline_width = 3 if is_collision else 1
            
            draw.polygon(rotated_points, fill=fill_color, outline=outline_color)
            
            # 設備情報の表示（オプション）
            if st.session_state.show_equipment_info:
                # 設備番号とラベル
                label = f"{i+1}: {equipment['label']}"
                # ラベルのサイズに応じてテキスト表示を調整
                text_width, text_height = draw.textsize(label, font=font)
                
                # テキストが設備内に収まるか確認
                if text_width < width_eq - 10 and text_height < length_eq - 10:
                    draw.text((x_eq - text_width/2, y_eq - text_height/2), label, fill="#000000", font=font)
                else:
                    # 収まらない場合は番号だけ
                    draw.text((x_eq - 5, y_eq - 5), str(i+1), fill="#000000", font=font)
        
        # 枠線
        draw.rectangle([0, 0, width_px-1, length_px-1], fill=None, outline="#000000", width=2)
        
        return factory_image
    
    # レイアウト図の表示
    st.subheader("工場レイアウト図")
    layout_image = render_layout()
    st.image(layout_image, use_column_width=True)
    
    # ダウンロードボタン
    layout_bytes = io.BytesIO()
    layout_image.save(layout_bytes, format='PNG')
    layout_bytes = layout_bytes.getvalue()
    
    st.download_button(
        label="レイアウト図をダウンロード",
        data=layout_bytes,
        file_name=f"{st.session_state.current_layout_name.replace(' ', '_')}.png",
        mime="image/png",
    )

    # 配置済み設備リスト
    st.subheader("配置済み設備一覧")
    if not st.session_state.equipment_list:
        st.info("設備がまだ配置されていません。サイドバーから設備を追加してください。")
    else:
        # 設備一覧をデータフレームとして表示
        equipment_data = []
        for i, eq in enumerate(st.session_state.equipment_list):
            equipment_data.append({
                "ID": i + 1,
                "設備名": eq["label"],
                "タイプ": equipment_defaults[eq["type"]]["label"],
                "幅 (m)": eq["width"],
                "長さ (m)": eq["length"],
                "X位置 (m)": eq["x"],
                "Y位置 (m)": eq["y"],
                "回転 (度)": eq["rotation"]
            })
        
        df = pd.DataFrame(equipment_data)
        st.dataframe(df)
        
        # 設備の編集と削除
        equipment_to_edit = st.selectbox("編集または削除する設備を選択", range(1, len(st.session_state.equipment_list) + 1), format_func=lambda x: f"{x}: {st.session_state.equipment_list[x-1]['label']}")
        
        if equipment_to_edit:
            eq_index = equipment_to_edit - 1
            selected_eq = st.session_state.equipment_list[eq_index]
            
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("選択した設備を編集"):
                    st.session_state.editing_equipment = eq_index
                    st.experimental_rerun()
            
            with col_delete:
                if st.button("選択した設備を削除"):
                    st.session_state.equipment_list.pop(eq_index)
                    st.success("設備を削除しました")
                    st.experimental_rerun()

# 設備編集モーダル（別途実装が必要）
if 'editing_equipment' in st.session_state:
    eq_index = st.session_state.editing_equipment
    eq = st.session_state.equipment_list[eq_index]
    
    st.sidebar.header(f"設備の編集: {eq['label']}")
    
    # 編集フォーム
    eq["label"] = st.sidebar.text_input("設備名", eq["label"])
    eq["width"] = st.sidebar.slider("幅 (m)", 0.5, 20.0, eq["width"], 0.5)
    eq["length"] = st.sidebar.slider("長さ (m)", 0.5, 20.0, eq["length"], 0.5)
    eq["color"] = st.sidebar.color_picker("色", eq["color"])
    eq["rotation"] = st.sidebar.slider("回転 (度)", 0, 359, eq["rotation"], 15)
    eq["x"] = st.sidebar.number_input("X位置 (m)", 0.0, st.session_state.factory_width, eq["x"], 0.5)
    eq["y"] = st.sidebar.number_input("Y位置 (m)", 0.0, st.session_state.factory_length, eq["y"], 0.5)
    
    if st.sidebar.button("変更を保存"):
        st.session_state.equipment_list[eq_index] = eq
        del st.session_state.editing_equipment
        st.sidebar.success("設備を更新しました")
        st.experimental_rerun()
    
    if st.sidebar.button("キャンセル"):
        del st.session_state.editing_equipment
        st.experimental_rerun()

# フッター
st.markdown("""
<div class="footer">
    <p>© 2025 工場レイアウトシミュレーター | Powered by Streamlit</p>
    <p>工場設備の配置や製造ラインの設計に活用してください。</p>
</div>
""", unsafe_allow_html=True)

# 使い方ガイド
with st.expander("使い方ガイド"):
    st.markdown("""
    ### 工場レイアウトシミュレーターの使い方
    
    1. **工場エリアの設定**
       - サイドバーで工場の幅と奥行きを設定します
       - 床の色を変更できます
       - グリッド表示や衝突検出表示をオン/オフできます
    
    2. **設備の追加**
       - 設備の種類を選択します
       - サイズ、色、回転角度を調整します
       - 設備名を入力します
       - 配置位置（X, Y）を指定します
       - 「設備を追加」ボタンをクリックします
    
    3. **設備の編集・削除**
       - 画面下部の設備一覧から編集したい設備を選択します
       - 「選択した設備を編集」ボタンをクリックして詳細を変更します
       - または「選択した設備を削除」ボタンで削除します
    
    4. **レイアウトの保存と読み込み**
       - レイアウト名を入力し「レイアウトを保存」をクリックします
       - 保存したレイアウトは「保存済みレイアウト」から選択して読み込めます
       - レイアウトはJSONファイルとしてエクスポート/インポートもできます
    
    5. **レイアウト図の保存**
       - 「レイアウト図をダウンロード」ボタンで現在のレイアウトを画像として保存できます
    
    ### 追加機能
    
    - **衝突検出**: 設備が重なっている場合、赤い枠線で表示されます
    - **統計情報**: 面積使用率や設備タイプ別の数などの情報を確認できます
    - **複数レイアウト管理**: 異なるレイアウトを保存・比較できます
    """)

# 開発者ノート
with st.expander("開発者ノート"):
    st.markdown("""
    ### 今後の改善予定機能
    
    - ドラッグ＆ドロップでの設備移動インターフェース
    - 3D表示オプション
    - 動線解析ツール
    - 設備間の接続/関係性の定義
    - レイアウトテンプレート機能
    - 設備タイプのカスタマイズオプション
    - 複数のレイアウト比較機能
    
    ### フィードバック
    
    このアプリケーションは継続的に改善されています。ご要望やバグ報告をいただければ幸いです。
    """)
