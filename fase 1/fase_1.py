import re
import os

def parse_grammar_file(file_path):
    sets = {}
    tokens = {}
    actions = {}
    errors = {}
    formato_correcto = True  #verificar si el formato es correcto
    tokens_present = False   # existe la sección TOKENS
    actions_brackets_balance = 0  # Contar en ACTIONS
    total_spaces = 0  # Contador de espacios en blanco
    total_enters = 0  # Contador de saltos de línea
    error_detectado = False  # Inicializar fuera del bucle
    tokens_checked = False #control para detectar 'TOKENS' solo una vez

    with open(file_path, 'r', encoding='utf-8') as file:
        current_section = None
        line_number = 0
        for line in file:
            line_number += 1
            stripped_line = line.strip()

            # Calcula la columna
            error_position = line.find('*')  # Encuentra el punto exacto del asterisco o el error
            if error_position != -1:
                column_number = error_position + 2
            else:
                column_number = len(line) - len(line.lstrip()) + len(stripped_line) + 1

            # Detectar sección principal
            if stripped_line == "SETS":
                current_section = "SETS"
            elif stripped_line == "TOKENS" and not tokens_checked:  # Detectar solo la palabra completa 'TOKENS' una vez
                current_section = "TOKENS"
                tokens_present = True  # Sección TOKENS presente
                tokens_checked = True  # Marcar que 'TOKENS' ha sido detectado correctamente
            elif stripped_line.startswith("TOKEN") and not error_detectado and not tokens_checked:  # Validar si hay error ortográfico y no se ha detectado 'TOKENS' correctamente aún
                if stripped_line.startswith("TOKEN") and "TOKENS" not in stripped_line:
                    error_position = line.find("TOKEN") + 1
                    print(f"Error de formato encontrado cerca de línea {line_number} columna {error_position + len('TOKEN')}: Falta la letra 'S' en 'TOKENS'")
                    formato_correcto = False
                    error_detectado = True  # Marcar que el error ya fue encontrado para no mostrar más
            elif stripped_line == "ACTIONS":
                current_section = "ACTIONS"
            elif stripped_line.startswith("ERROR"):
                current_section = "ERROR"
            elif stripped_line == "":
                continue  # Ignorar líneas en blanco

            # Parsear cada sección basado en la sección actual
            try:
                if current_section == "SETS":
                    parse_set(stripped_line, sets, line_number, column_number)
                elif current_section == "TOKENS":
                    parse_token(stripped_line, tokens, line_number, column_number)
                elif current_section == "ACTIONS":
                    # Contamos las llaves para asegurarnos de que coincidan
                    actions_brackets_balance += stripped_line.count("{") - stripped_line.count("}")
                    parse_action(stripped_line, actions, line_number, column_number)
                elif current_section == "ERROR":
                    parse_error(stripped_line, errors, line_number, column_number)
            except ValueError as salida:
                print(f"Error de formato encontrado cerca de línea {line_number} columna {column_number}: {salida}")
                formato_correcto = False  # Marcar como incorrecto si hay un error de formato

    # Validar si todas las secciones obligatorias existen

    if actions_brackets_balance != 0:
        print(f"Error: Las llaves de la sección ACTIONS no están balanceadas.")
        formato_correcto = False

    if formato_correcto:
        print("Formato correcto")
    else:
        print("Formato incorrecto")

    return formato_correcto

# Las funciones parse_set, parse_token, parse_action y parse_error siguen igual.

def parse_set(line, sets, line_number, column_number):
    if line.startswith("SETS") or line == "":
        return  # Ignorar la línea de encabezado o vacía
    match = re.match(r'(\w+)\s*=\s*(.+)', line)
    if match:
        set_name, set_definition = match.groups()
        set_definition = set_definition.replace("CHR", "").strip()

        # Validar que los paréntesis estén balanceados
        if set_definition.count('(') != set_definition.count(')'):
            raise ValueError(f"Paréntesis desbalanceados en SET")
        
        sets[set_name] = set_definition
    else:
        raise ValueError(f"Formato incorrecto en SET")

def parse_token(line, tokens, line_number, column_number):
    if line.startswith("TOKENS") or line == "":
        return  # Ignorar la línea de encabezado o vacía
    match = re.match(r'TOKEN\s+(\d+)\s*=\s*(.+)', line)
    if match:
        token_number, token_definition = match.groups()

        # Validar caso especial de asterisco con una comilla simple
        if token_definition == "'*'":
            tokens[token_number] = token_definition
            return

        # Ignorar paréntesis dentro de comillas simples
        paren_in_quotes = re.findall(r"'.*?'", token_definition)
        cleaned_token = token_definition
        for quoted in paren_in_quotes:
            cleaned_token = cleaned_token.replace(quoted, '')  # Remover contenido entre comillas simples

        # Validar que las comillas simples estén balanceadas
        if token_definition.count('\'') % 2 != 0:
            raise ValueError(f"Comillas desbalanceadas en TOKEN")
        
        # Validar que los paréntesis estén balanceados en el token ya limpio
        if cleaned_token.count('(') != cleaned_token.count(')'):
            raise ValueError(f"Paréntesis desbalanceados en TOKEN")
        
        tokens[token_number] = token_definition
    else:
        raise ValueError(f"Formato incorrecto en TOKEN")


def parse_action(line, actions, line_number, column_number):
    if line.startswith("ACTIONS") or line == "":
        return  # Ignorar la línea de encabezado o vacía
    if line.startswith("RESERVADAS"):
        actions['RESERVADAS'] = {}
    elif '=' in line and line.count('\'') >= 2:  # Solo considerar líneas con asignación y comillas
        match = re.match(r'(\d+)\s*=\s*\'(.+?)\'', line)
        if match:
            action_number, action_value = match.groups()

            # Validar si la línea tiene un formato correcto con las comillas necesarias
            if line.count('\'') % 2 != 0:
                raise ValueError(f"Comillas desbalanceadas en ACTIONS")
            
            actions['RESERVADAS'][action_number] = action_value
        else:
            raise ValueError(f"Formato incorrecto en ACTIONS")
    # Ignorar las llaves, ya que las estamos contando fuera para verificar el balance

def parse_error(line, errors, line_number, column_number):
    if line.startswith("ERROR") or line == "":
        return  # Ignorar la línea de encabezado o vacía
    match = re.match(r'ERROR\s*=\s*(\d+)', line)
    if match:
        error_number = match.group(1)
        errors[error_number] = "ERROR"
    else:
        raise ValueError(f"Formato incorrecto en ERROR")

# Prueba del programa con un archivo
if __name__ == "__main__":
    # Ruta del archivo de gramática
    file_path = r'C:\Users\aldan\OneDrive\Documentos\Universidad\4to Semestre\Lenguajes Formales y Automatas\Proyecto\prueba_4.txt'

    # Comprobación de la existencia del archivo
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe.")
    else:
        # Parsear el archivo de gramática
        formato_correcto = parse_grammar_file(file_path)