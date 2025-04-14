import os
import pandas as pd
import plotly.express as px
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def process_sales_data(file_path):
    """Process the uploaded sales data and generate trends."""
    try:
        df = pd.read_excel(file_path)

        # Debug: Print actual column names
        print("Columns in uploaded file:", df.columns)

        # Standardizing column names
        df.columns = df.columns.astype(str).str.strip().str.lower()

        required_columns = {'date', 'order_value_eur'}
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise KeyError(f"Missing columns: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns)}")

        # Ensure 'date' is in proper format
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)

        # ✅ Convert 'month' to string for visualization
        df['month'] = df['date'].dt.strftime("%Y-%m")

        # Daily Sales Trend
        daily_sales = df.groupby('date', as_index=False)['order_value_eur'].sum()
        daily_trend = px.line(daily_sales, x='date', y='order_value_eur', title="Daily Sales Trend")

        # Monthly Sales Trend
        monthly_sales = df.groupby('month', as_index=False)['order_value_eur'].sum()
        monthly_trend = px.bar(monthly_sales, x='month', y='order_value_eur', title="Monthly Sales Trend")

        # Seasonal Sales Trend
        df['season'] = df['date'].dt.month % 12 // 3 + 1
        seasonal_sales = df.groupby('season', as_index=False)['order_value_eur'].sum()
        seasonal_trend = px.pie(seasonal_sales, values='order_value_eur', names='season', title="Seasonal Sales Trend")

        return df.to_html(), daily_trend.to_html(), monthly_trend.to_html(), seasonal_trend.to_html()

    except Exception as e:
        return f"<p>Error processing file: {e}</p>", None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    sales_data, daily_trend, monthly_trend, seasonal_trend = None, None, None, None

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            sales_data, daily_trend, monthly_trend, seasonal_trend = process_sales_data(file_path)

            # Remove uploaded file after processing to save space
            os.remove(file_path)

    return render_template("dashboard.html",
                           sales_data=sales_data,
                           daily_sales_trend=daily_trend,
                           monthly_sales_trend=monthly_trend,
                           seasonal_sales_trend=seasonal_trend)

if __name__ == "__main__":
    app.run(debug=True)
