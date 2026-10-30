import json
import os
import streamlit as st
from openai import OpenAI

# إعداد الصفحة
st.set_page_config(
    page_title="مساعد الدخل الذكي", page_icon="💰", layout="centered"
)

FILE_NAME = "money_data.json"


# تحميل البيانات المالية
def load_data():
  if os.path.exists(FILE_NAME):
    try:
      with open(FILE_NAME, "r", encoding="utf-8") as file:
        return json.load(file)
    except (json.JSONDecodeError, OSError):
      pass
  return {"income": 0.0, "expenses": []}


# حفظ البيانات المالية
def save_data(data):
  with open(FILE_NAME, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)


# تهيئة البيانات
if "data" not in st.session_state:
  st.session_state.data = load_data()

data = st.session_state.data

# قراءة مفتاح OpenAI بأمان من إعدادات Streamlit Secrets
openai_api_key = None
try:
  if "OPENAI_API_KEY" in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
  pass

# العنوان الرئيسي
st.title("💰 مساعد الدخل الذكي")

# القائمة الجانبية للتنقل
menu = st.sidebar.selectbox(
    "القائمة الرئيسية",
    [
        "الرئيسية",
        "إضافة مصروف",
        "سجل المصروفات",
        "تعديل الدخل",
        "مساعد الذكاء الاصطناعي (شات)",
        "فرص جني المال",
    ],
)

# حساب المجموع
total_income = data.get("income", 0.0)
total_expenses = sum(item["amount"] for item in data.get("expenses", []))
remaining = total_income - total_expenses

# 1. الصفحة الرئيسية
if menu == "الرئيسية":
  st.subheader("📊 ملخص الميزانية")
  col1, col2 = st.columns(2)
  with col1:
    st.metric(label="إجمالي الدخل", value=f"{total_income:,.2f} ر.س")
  with col2:
    st.metric(label="إجمالي المصروفات", value=f"{total_expenses:,.2f} ر.س")

  st.metric(label="المبلغ المتبقي", value=f"{remaining:,.2f} ر.س")

  st.markdown("---")
  st.markdown("### ⚡ ملخص سريع")
  st.write(f"• إجمالي عدد العمليات المسجلة: {len(data['expenses'])} عمليات")

# 2. إضافة مصروف
elif menu == "إضافة مصروف":
  st.subheader("➕ تسجيل مصروف جديد")
  with st.form("expense_form"):
    title = st.text_input("اسم المصروف أو البند")
    amount = st.number_input("المبلغ (ر.س)", min_value=0.0, step=1.0)
    category = st.selectbox(
        "التصنيف", ["طعام", "مواصلات", "فواتير", "تسوّق", "أخرى"]
    )
    submit = st.form_submit_button("حفظ المصروف")

    if submit:
      if title and amount > 0:
        data["expenses"].append(
            {"title": title, "amount": amount, "category": category}
        )
        save_data(data)
        st.success("تم إضافة المصروف بنجاح!")
      else:
        st.warning("الرجاء إدخال اسم صحيح ومبلغ أكبر من الصفر.")

# 3. سجل المصروفات
elif menu == "سجل المصروفات":
  st.subheader("📋 سجل العمليات السابقة")
  expenses = data.get("expenses", [])
  if not expenses:
    st.info("لا توجد مصروفات مسجلة حتى الآن.")
  else:
    for i, exp in enumerate(reversed(expenses)):
      st.write(
          f"🔹 **{exp['title']}** - {exp['amount']} ر.س ({exp['category']})"
      )

    if st.button("حذف أحدث مصروف أُضيف"):
      data["expenses"].pop()
      save_data(data)
      st.success("تم حذف آخر عملية بنجاح!")
      st.rerun()

# 4. تعديل الدخل
elif menu == "تعديل الدخل":
  st.subheader("⚙️ تحديث الدخل الشهري")
  new_income = st.number_input(
      "قيمة الدخل الجديدة (ر.س)", value=float(total_income), step=100.0
  )
  if st.button("تحديث الدخل"):
    data["income"] = new_income
    save_data(data)
    st.success("تم تحديث الدخل بنجاح!")
    st.rerun()

# 5. مساعد الذكاء الاصطناعي (شات متواصل)
elif menu == "مساعد الذكاء الاصطناعي (شات)":
  st.subheader("🤖 الشات الذكي مع المساعد المالي")
  st.write(
      "تحدث بحرية واسأل عن ميزانيتك أو أفكار لزيادة الدخل؛ المحادثة مستمرة ولا"
      " تُحذف أثناء تنقلك في الشات."
  )

  if not openai_api_key:
    st.warning(
        "⚠️ مفتاح OpenAI API غير مضبوط في إعدادات Streamlit Secrets. يرجى"
        " إضافته من لوحة التحكم."
    )
  else:
    # تهيئة سجل رسائل الشات في الجلسة إذا لمש يكن موجوداً
    if "messages" not in st.session_state:
      st.session_state.messages = [{
          "role": "system",
          "content": (
              "أنت مساعد مالي ذكي ومحترف تساعد المستخدم علاء في إدارة أمواله"
              " وزيادة دخله وتقديم أفكار مشاريع رقمية."
          ),
      }]

    # عرض الرسائل السابقة في الشات (باستثناء رسالة الـ system)
    for message in st.session_state.messages:
      if message["role"] != "system":
        with st.chat_message(message["role"]):
          st.markdown(message["content"])

    # استقبال رسالة المستخدم الجديدة عبر شريط الشات التفاعلي
    if prompt := st.chat_input("اكتب رسالتك أو سؤالك هنا..."):
      # إضافة رسالة المستخدم وسجلها
      st.session_state.messages.append({"role": "user", "content": prompt})
      with st.chat_message("user"):
        st.markdown(prompt)

      # توليد الرد من نموذج OpenAI
      try:
        client = OpenAI(api_key=openai_api_key)
        with st.chat_message("assistant"):
          with st.spinner("جاري التفكير والكتابة..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=st.session_state.messages
            )
            bot_reply = response.choices[0].message.content
            st.markdown(bot_reply)

          # حفظ رد المساعد في السجل
          st.session_state.messages.append(
              {"role": "assistant", "content": bot_reply}
          )
      except Exception as e:
        st.error(f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")

# 6. فرص جني المال
elif menu == "فرص جني المال":
  st.subheader("🚀 أفكار لزيادة دخلك")
  st.write(
      "بناءً على تحليلي لميزانيتك ومصاريفك، يمكنك استغلال مهاراتك الرقمية أو"
      " تقديم استشارات جانبية لزيادة التدفق النقدي."
  )
  st.info(
      "💡 نصيحة: حاول توجيه 20% من فائض دخلك نحو الادخار أو الاستثمار الرقمي"
      " المصغر."
  )
