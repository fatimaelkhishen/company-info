from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

form_html = """
<!doctype html>
<html>
<head>
    <title>Company Job Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
        .box { background: #fff; padding: 15px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
        h3 { margin-top: 0; font-family: 'Verdana', sans-serif; color: #333; }
        input, select, textarea { width: 100%; padding: 6px; margin: 5px 0 10px 0; box-sizing: border-box; font-family: 'Arial', sans-serif; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        td { padding: 5px; vertical-align: top; }
        input[type="submit"] { width: auto; background: #007BFF; color: #fff; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; font-size: 14px; }
        input[type="submit"]:hover { background: #0056b3; }
        pre { background: #eee; padding: 10px; border-radius: 6px; }
    </style>
</head>
<body>

<form method="POST">

<div class="box">
    <h3>Basic Info</h3>
    <label>Link</label>
    <input type="url" name="Link" placeholder="https://company.com/jobs/12345">
    
    <label>Job Title</label>
    <input type="text" name="Job_Title" placeholder="Software Engineer">
    
    <label>Company Name</label>
    <input type="text" name="Company_Name" placeholder="ABC Technologies">
    
    <label>Country</label>
    <select name="Country">
        <option value="">Select Country</option>
        <option>Lebanon</option>
        <option>Bahrain</option>
        <option>Qatar</option>
        <option>Jordan</option>
        <option>Other</option>
    </select>
    
    <label>City</label>
    <input type="text" name="City" placeholder="Kuwait City">
    
    <label>Posting Date</label>
    <input type="date" name="Posting_Date">
</div>

<div class="box">
    <h3>Industry & Degree</h3>
    <table border="1">
        <tr>
            <td>Industry</td>
            <td>Degree Required</td>
        </tr>
        <tr>
            <td>
                <select name="Industry">
                    <option value="">Select Industry</option>
                    <option>Information Technology</option>
                    <option>Finance</option>
                    <option>Healthcare</option>
                    <option>Education</option>
                    <option>Engineering</option>
                    <option>Retail</option>
                    <option>Other</option>
                </select>
            </td>
            <td>
                <select name="Degree">
                    <option value="">Select Degree</option>
                    <option>High School</option>
                    <option>Diploma</option>
                    <option>Bachelor's</option>
                    <option>Master's</option>
                    <option>PhD</option>
                    <option>Not specified</option>
                </select>
            </td>
        </tr>
    </table>
</div>

<div class="box">
    <h3>Experience & Compensation</h3>
    <table border="1">
        <tr>
            <td>Gender</td>
            <td>Years of Experience</td>
            <td>Salary Range</td>
        </tr>
        <tr>
            <td>
                <select name="Gender">
                    <option value="">Select Gender</option>
                    <option>Not specified</option>
                    <option>Male</option>
                    <option>Female</option>
                </select>
            </td>
            <td><input type="text" name="Years_of_Experience" placeholder="2-4"></td>
            <td><input type="text" name="Salary_Range" placeholder="800-1200 KWD"></td>
        </tr>
    </table>
</div>

<div class="box">
    <h3>Job Description</h3>
    <textarea name="Job_Description" rows="8" placeholder="Full job description here..."></textarea>
</div>

<input type="submit" value="Submit">

{% if data %}
<div class="box">
    <h3>Submitted Data:</h3>
    <pre>{{ data }}</pre>
</div>
{% endif %}

</form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def form():
    submitted_data = None
    if request.method == "POST":
        submitted_data = request.form.to_dict()
    return render_template_string(form_html, data=submitted_data)

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT, debug=True)
