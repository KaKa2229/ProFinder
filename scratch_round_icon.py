from PIL import Image, ImageDraw
import os

def crop_to_circle(input_path, output_path):
    # Abrir imagem e garantir que tem canal alpha
    img = Image.open(input_path).convert("RGBA")
    
    # Criar máscara circular (antialiased)
    # Aumentar tamanho para fazer downsampling para antialiasing mais suave
    mask_size = (img.size[0] * 4, img.size[1] * 4)
    mask = Image.new("L", mask_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + mask_size, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    
    # Aplicar máscara
    rounded = img.copy()
    rounded.putalpha(mask)
    
    # Salvar PNG arredondado
    rounded.save(output_path, "PNG")
    
    # Gerar favicon.ico também arredondado
    favicon_path = os.path.join(os.path.dirname(output_path), 'favicon.ico')
    rounded.save(favicon_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"Ícone arredondado salvo em {output_path} e {favicon_path}")

# Processar icon-192x192
icon_192 = 'app/static/img/icons/icon-192x192.png'
if os.path.exists(icon_192):
    # Fazer backup do original caso seja necessário
    backup_path = icon_192 + '.bak'
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy(icon_192, backup_path)
    
    crop_to_circle(backup_path, icon_192)

# Fazer o mesmo para o 512x512 para manter consistência do PWA
icon_512 = 'app/static/img/icons/icon-512x512.png'
if os.path.exists(icon_512):
    backup_path_512 = icon_512 + '.bak'
    if not os.path.exists(backup_path_512):
        import shutil
        shutil.copy(icon_512, backup_path_512)
        
    crop_to_circle(backup_path_512, icon_512)
