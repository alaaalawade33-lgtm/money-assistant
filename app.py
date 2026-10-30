import json
import os
from datetime import datetime
import streamlit as st
import requests

st.set_page_config(page_title="AI Money Assistant", page_icon="💰", layout="centered")

FILE_NAME = "money_data.json"
PROFILE_FILE = "income_profile.json"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


CATEGORIES = ["طعام", "مواصلات", "تسوق", "فواتير", "ترفيه", "صحة", "تعليم", "أخرى"]

def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    data.setdefault("income", 0)
    data.setdefault("expenses", [])
    return data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def load_profile():
    default = {"skills": "", "hours": 5, "capital": 0, "mode": "عن بُعد", "target": 1000}
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as file:
                default.update(json.load(file))
        except (json.JSONDecodeError, OSError):
            pass
    return default

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as file:
        json.dump(profile, file, ensure_ascii=False, indent=4)

data = load_data()
profile = load_profile()

st.title("💰 مساعد الدخل الذكي")

# القائمة الجانبية المحدثة لتشمل الذكاء الاصطناعي وفرص المال
menu = st.sidebar.selectbox(
    "القائمة الرئيسية", 
    ["🏠 الرئيسية", "➕ إضافة مصروف", "📋 سجل المصروفات", "⚙️ تعديل الدخل", "🤖 مساعد الذكاء الاصطناعي", "🚀 فرص جني المال"]
)

# 1. الرئيسية
if menu == "🏠 الرئيسية":
    income = float(data.get("income", 0))
    total_expenses = sum(float(e.get("amount", 0)) for e in data.get("expenses", []))
    balance = income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الدخل", f"{income:.2f} ر.س")
    col2.metric("المصروفات", f"{total_expenses:.2f} ر.س")
    col3.metric("المتبقي", f"{balance:.2f} ر.س", delta_color="inverse")
    
    st.divider()
    st.subheader("📊 ملخص سريع")
    if data.get("expenses"):
        st.write(f"إجمالي عدد العمليات المسجلة: {len(data['expenses'])} عمليات.")
        by_cat = {}
        for e in data["expenses"]:
            c = e.get("category", "أخرى")
            by_cat[c] = by_cat.get(c, 0) + float(e.get("amount", 0))
        for cat, amount in by_cat.items():
            st.write(f"- **{cat}**: {amount:.2f} ر.س")
    else:
        st.info("لا توجد مصروفات مسجلة حتى الآن.")

# 2. إضافة مصروف
elif menu == "➕ إضافة مصروف":
    st.subheader("إضافة مصروف جديد")
    with st.form("expense_form"):
        name = st.text_input("اسم المصروف (مثال: وجبة غداء)")
        amount = st.number_input("المبلغ (بالريال)", min_value=0.0, step=1.0)
        category = st.selectbox("التصنيف", CATEGORIES)
        submit = st.form_submit_button("حفظ المصروف")
        
        if submit:
            if name and amount > 0:
                new_exp = {
                    "name": name,
                    "amount": amount,
                    "category": category,
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
                data["expenses"].append(new_exp)
                save_data(data)
                st.success("تم حفظ المصروف بنجاح! ✅")
            else:
                st.warning("الرجاء إدخال اسم صحيح ومبلغ أكبر من الصفر.")

# 3. سجل المصروفات
elif menu == "📋 سجل المصروفات":
    st.subheader("سجل المصروفات السابقة")
    if data.get("expenses"):
        for i, e in enumerate(data["expenses"]):
            st.write(f"**{i+1}. {e.get('name')}** — {e.get('amount')} ر.س ({e.get('category')}) [التاريخ: {e.get('date')}]")
        
        if st.button("🗑️ حذف آخر مصروف"):
            data["expenses"].pop()
            save_data(data)
            st.rerun()
    else:
        st.info("لا توجد مصروفات مسجلة.")

# 4. تعديل الدخل
elif menu == "⚙️ تعديل الدخل":
    st.subheader("تحديث الدخل الشهري")
    new_income = st.number_input("أدخل دخلك الشهري الجديد (ريال):", value=float(data.get("income", 0)), step=100.0)
    if st.button("تحديث الدخل"):
        data["income"] = new_income
        save_data(data)
        st.success("تم تحديث الدخل بنجاح! ✅")

# 5. مساعد الذكاء الاصطناعي
elif menu == "🤖 مساعد الذكاء الاصطناعي":
    st.subheader("🤖 اسأل مساعد الذكاء الاصطناعي")
    st.write("استشر المساعد في تحسين ميزانيتك، تسعير خدماتك، أو تقليل المصروفات.")
    
    question = st.text_input("اكتب سؤالك هنا:", value="اقترح لي طريقة لتقليل مصاريفي بناءً على دخلي الحالي")
    if st.button("إرسال للسؤال"):
        if OPENAI_API_KEY and OPENAI_API_KEY != "sk-...":
            with st.spinner("جاري التفكير والرد..."):
                try:
                    income = float(data.get("income", 0))
                    total_exp = sum(float(e.get("amount", 0)) for e in data.get("expenses", []))
                    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": f"أنت مساعد مالي ذكي. دخل المستخدم {income} ريال ومصروفاته {total_exp} ريال."},
                            {"role": "user", "content": question}
                        ]
                    }
                    res = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=25)
                    if res.status_code == 200:
                        answer = res.json()['choices'][0]['message']['content']
                        st.info(answer)
                    else:
                        st.error("⚠️ خطأ في الاستجابة من خادم الذكاء الاصطناعي.")
                except Exception as ex:
                    st.error(f"⚠️ خطأ في الاتصال: {ex}")
        else:
            st.warning("⚠️ مفتاح OpenAI API غير مضبوط في الكود.")

# 6. فرص جني المال
elif menu == "🚀 فرص جني المال":
    st.subheader("🚀 المساعد الذكي لجني الأموال")
    skills = st.text_input("مهاراتك (مثال: برمجة، تصميم، كتابة):", value=profile.get("skills", ""))
    hours = st.number_input("ساعات العمل أسبوعياً:", value=int(profile.get("hours", 5)))
    capital = st.number_input("رأس المال المتاح (ريال):", value=float(profile.get("capital", 0)))
    target = st.number_input("الهدف الشهري المرغوب (ريال):", value=float(profile.get("target", 1000)))
    mode = st.selectbox("طريقة العمل المفضلة:", ["عن بُعد", "حضوري", "كلاهما"], index=0 if profile.get("mode")=="عن بُعد" else 1)
    
    if st.button("حفظ وتوليد خطة الأفكار"):
        profile = {"skills": skills, "hours": hours, "capital": capital, "mode": mode, "target": target}
        save_profile(profile)
        st.success("تم حفظ ملفك الشخصي بنجاح! ✅")
        
        st.markdown("### 💡 أفكار مقترحة بناءً على مهاراتك:")
        if "برمجة" in skills or "python" in skills.lower():
            st.write("• **تطوير أدوات مصغرة للشركات والأفراد:** تقديم سكريبتات أو أدوات أتمتة بسيطة.")
        elif "تصميم" in skills or "تصميم" in skills:
            st.write("• **تصميم محتوى المنصات الرقمية:** تصميم تصاميم مخصصة للأعمال الناشئة.")
        else:
            st.write("• **تقديم خدمات رقمية مصغرة:** استغلال مهاراتك في تقديم خدمات مستقلة عبر الإنترنت.")
        st.write(f"🎯 لهدف شهري بقيمة {target} ريال، حاول تحقيق ما يقارب {target/4:.0f} ريال أسبوعياً.")
