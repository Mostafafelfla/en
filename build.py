import os
import json
import shutil
from bs4 import BeautifulSoup

# --- 1. الإعدادات والمسارات ---
BASE_DIR = "public"
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
JS_FILE_NAME = "offline_logic.js"
JS_FILE_PATH = os.path.join(ASSETS_DIR, JS_FILE_NAME)

SECTION_FILES = {
    "Listening": "listening-test-instruction.html",
    "Reading": "reading-test-instruction.html",
    "Writing": "writing-test-instruction.html",
    "Speaking": "speaking-test-instruction.html"
}

LINK_MAPPING = {
    "/listening/": "Listening/listening-test-instruction.html",
    "/reading/": "Reading/reading-test-instruction.html",
    "/writing/": "Writing/writing-test-instruction.html",
    "/speaking/": "Speaking/speaking-test-instruction.html",
    "/complete-test-instruction/": "Complete/complete-test-instruction.html"
}

NEXT_SECTION_MAPPING = {
    "../Listening/part_001.html": "../Listening/listening-test-instruction.html",
    "../Reading/part_001.html": "../Reading/reading-test-instruction.html",
    "../Writing/part_001.html": "../Writing/writing-test-instruction.html",
    "../Speaking/part_001.html": "../Speaking/speaking-test-instruction.html"
}

# --- 2. التنظيف وإصلاح الروابط وتعديل الأسماء ---
def clean_and_fix():
    print("🧹 جاري تنظيف الموقع وإصلاح الروابط...")
    
    # الخطوة أ: إعادة تسمية ملفات part_001.html
    for root, dirs, files in os.walk(BASE_DIR):
        folder_name = os.path.basename(root)
        if "Exam_" in root:
            for sec, target in SECTION_FILES.items():
                if sec in root:
                    p1 = os.path.join(root, "part_001.html")
                    pt = os.path.join(root, target)
                    if os.path.exists(p1):
                        os.rename(p1, pt)

    # الخطوة ب: تعديل محتوى ملفات HTML
    for root, dirs, files in os.walk(BASE_DIR):
        for file_name in files:
            if not file_name.endswith(".html"): continue
            file_path = os.path.join(root, file_name)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")
                modified = False

                # 1. إزالة Complete Test وتصحيح روابط take-exam
                if file_name == "take-exam.html":
                    for a in soup.find_all("a", class_="dropdown-item"):
                        href = a.get("href", "")
                        if "Complete Test" in a.text or "complete-test" in href:
                            li = a.find_parent("li")
                            if li: li.decompose()
                            else: a.decompose()
                            modified = True
                        else:
                            for key, correct_path in LINK_MAPPING.items():
                                if key in href:
                                    a["href"] = correct_path
                                    modified = True
                                    break

                # 2. تغيير الاسم إلى Moaz في الداشبورد
                if file_name == "student-dashboard.html":
                    for p in soup.find_all("p"):
                        if p.text and "Welcome to" in p.text:
                            b = p.find("b")
                            if b:
                                b.string = "z"
                                modified = True

                # 3. إزالة الروابط الزائدة من الـ Navbar
                for a in soup.find_all("a", class_="nav-link"):
                    if a.text and a.text.strip() in ["My Marks", "Billing", "Logout"]:
                        li = a.find_parent("li", class_="nav-item")
                        if li: li.decompose()
                        else: a.decompose()
                        modified = True

                # 4. ربط الأقسام ببعضها (زر Next)
                for a in soup.find_all("a", href=True):
                    if a["href"] in NEXT_SECTION_MAPPING:
                        a["href"] = NEXT_SECTION_MAPPING[a["href"]]
                        modified = True

                if modified:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(str(soup))
            except Exception as e:
                print(f"⚠️ خطأ في معالجة {file_path}: {e}")

# --- 3. بناء خريطة الأسئلة الذكية ---
def build_master_map():
    print("🗺️ جاري مسح الامتحانات لبناء 'خريطة الأسئلة' الدقيقة...")
    master_map = {}
    for root, dirs, files in os.walk(BASE_DIR):
        path_parts = root.split(os.sep)
        exam = next((p for p in path_parts if p.startswith("Exam_")), None)
        section = next((p for p in path_parts if p in ["Listening", "Reading", "Writing", "Speaking"]), None)

        if exam and section:
            if exam not in master_map: master_map[exam] = {}
            if section not in master_map[exam]: master_map[exam][section] = []

            # استخراج ملفات الأسئلة وترتيبها
            part_files = [f for f in files if (f.startswith("part_") or f.endswith("-instruction.html")) and f.endswith(".html")]
            part_files.sort() 

            for f in part_files:
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, "r", encoding="utf-8") as html_f:
                        soup = BeautifulSoup(html_f, "html.parser")
                        
                        # تتبع أسئلة الاستماع
                        radios = soup.find_all("input", type="radio")
                        if radios:
                            names = list(set([r.get("name") for r in radios if r.get("name")]))
                            names.sort()
                            for name in names:
                                master_map[exam][section].append(f"{f}_radio_{name}")
                                
                        # تتبع أسئلة القراءة
                        selects = soup.find_all("select")
                        if selects:
                            for i, sel in enumerate(selects):
                                padded_index = str(i).zfill(2)
                                master_map[exam][section].append(f"{f}_select_{padded_index}")
                except: pass
    return master_map

# --- 4. زراعة العقل الأوفلاين ---
def inject_offline_logic():
    master_map = build_master_map()
    map_json = json.dumps(master_map)
    
    js_code = f"""
    const MASTER_MAP = {map_json};

    document.addEventListener("DOMContentLoaded", () => {{
        const pathParts = window.location.pathname.split('/');
        const fileName = pathParts.pop(); 
        const section = pathParts.pop(); 
        const exam = pathParts.pop(); 

        if (fileName.startsWith('part_') || fileName.includes('-test-instruction')) {{
            const radios = document.querySelectorAll('input[type="radio"]');
            radios.forEach(radio => {{
                const baseKey = `${{exam}}_${{section}}_${{fileName}}_radio_${{radio.name}}`;
                if (localStorage.getItem(baseKey) === radio.id) radio.checked = true;
                radio.addEventListener('change', function() {{
                    localStorage.setItem(baseKey, this.id);
                    let label = document.querySelector(`label[for="${{this.id}}"]`);
                    let text = label ? label.innerText.replace(/Option [A-Z]:\\s*/ig, '').trim() : this.value;
                    localStorage.setItem(baseKey + '_text', text);
                }});
            }});

            const selects = document.querySelectorAll('select');
            selects.forEach((sel, index) => {{
                const paddedIndex = String(index).padStart(2, '0');
                const baseKey = `${{exam}}_${{section}}_${{fileName}}_select_${{paddedIndex}}`;
                let savedValue = localStorage.getItem(baseKey);
                if (savedValue) {{
                    sel.value = savedValue;
                    if(window.jQuery) $(sel).trigger('change');
                }}
                sel.addEventListener('change', function() {{
                    localStorage.setItem(baseKey, this.value);
                    let selectedOption = this.options[this.selectedIndex];
                    localStorage.setItem(baseKey + '_text', selectedOption.text.trim());
                    localStorage.setItem(baseKey + '_val', selectedOption.value.trim());
                }});
            }});

            const textareas = document.querySelectorAll('textarea');
            textareas.forEach(ta => {{
                const baseKey = `${{exam}}_${{section}}_${{fileName}}_${{ta.name || 'textarea'}}`;
                if (localStorage.getItem(baseKey)) {{
                    ta.value = localStorage.getItem(baseKey);
                    ta.dispatchEvent(new Event('input'));
                }}
                ta.addEventListener('input', function() {{
                    localStorage.setItem(baseKey, this.value);
                }});
            }});
        }}

        if (fileName === 'answer-key.html') {{
            const rows = document.querySelectorAll('#dev-table tr');
            let score = 0;
            let expectedKeys = [];
            if (MASTER_MAP[exam] && MASTER_MAP[exam][section]) {{
                expectedKeys = MASTER_MAP[exam][section];
            }}
            
            rows.forEach((row, index) => {{
                if (index === 0) return;
                const tds = row.querySelectorAll('td');
                if (tds.length >= 4) {{
                    const correctAnsOriginal = tds[1].innerText.trim();
                    const correctAns = correctAnsOriginal.toLowerCase();
                    const studentAnsCell = tds[2];
                    const iconCell = tds[3];
                    let studentAnsDisplay = "No Answer";
                    let isCorrect = false;

                    let qIndex = index - 1; 
                    if (qIndex < expectedKeys.length) {{
                        let baseKey = `${{exam}}_${{section}}_${{expectedKeys[qIndex]}}`;
                        let savedText = localStorage.getItem(baseKey + '_text');
                        let savedVal = localStorage.getItem(baseKey + '_val');

                        if (savedText && savedText !== "None" && savedText !== "") {{
                            studentAnsDisplay = savedText;
                            let studentLower = savedText.toLowerCase();
                            
                            if (correctAnsOriginal.length === 1 && /^[A-E]$/i.test(correctAnsOriginal)) {{
                                 if (savedVal && savedVal.startsWith("Option")) {{
                                     let optionNum = savedVal.replace("Option", "");
                                     let optionLetter = String.fromCharCode(64 + parseInt(optionNum)).toLowerCase();
                                     studentAnsDisplay = String.fromCharCode(64 + parseInt(optionNum));
                                     if (optionLetter === correctAns) isCorrect = true;
                                 }}
                            }} else {{
                                if (studentLower === correctAns || correctAns.includes(studentLower) || studentLower.includes(correctAns)) {{
                                    isCorrect = true;
                                }}
                            }}
                        }}
                    }}
                    
                    studentAnsCell.innerText = studentAnsDisplay;
                    if (isCorrect) {{
                        score++;
                        iconCell.innerHTML = '<i class="fa fa-check" style="color: green; font-size: 1.2em;"></i>';
                    }} else {{
                        iconCell.innerHTML = '<i class="fa fa-close" style="color: red; font-size: 1.2em;"></i>';
                    }}
                }}
            }});
            localStorage.setItem(`${{exam}}_${{section}}_Score`, score);
        }}

        if (fileName === 'result.html') {{
            const score = localStorage.getItem(`${{exam}}_${{section}}_Score`) || "0";
            const rows = document.querySelectorAll('#dev-table tr');
            if(rows.length > 1) {{
                const tds = rows[1].querySelectorAll('td');
                if(tds.length >= 3) {{
                    tds[1].innerText = score;
                    let clb = "M";
                    let s = parseInt(score);
                    if (section === "Listening" || section === "Reading") {{
                        if (s >= 35) clb = "10-12";
                        else if (s >= 31) clb = "9";
                        else if (s >= 28) clb = "8";
                        else if (s >= 24) clb = "7";
                        else if (s >= 20) clb = "6";
                        else if (s >= 15) clb = "5";
                        else if (s >= 10) clb = "4";
                        else if (s >= 0) clb = "3";
                    }}
                    tds[2].innerText = clb;
                }}
            }}
        }}
    }});
    """

    print(f"⚙️ جاري تحديث ملف العقل الأوفلاين ({JS_FILE_NAME})...")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(JS_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(js_code)

    print("💉 جاري زراعة الكود في صفحات الموقع...")
    for root, dirs, files in os.walk(BASE_DIR):
        for file_name in files:
            if not file_name.endswith(".html"): continue
            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")
                
                rel_asset_path = os.path.relpath(JS_FILE_PATH, root).replace('\\', '/')
                script_exists = False
                for script in soup.find_all("script"):
                    if script.get("src") == rel_asset_path:
                        script_exists = True
                        break
                        
                if not script_exists:
                    new_script = soup.new_tag("script", src=rel_asset_path)
                    if soup.body:
                        soup.body.append(new_script)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(str(soup))
            except Exception as e:
                pass

if __name__ == "__main__":
    clean_and_fix()
    inject_offline_logic()
    print("✅ تمت جميع العمليات بنجاح! الموقع جاهز للنشر.")
