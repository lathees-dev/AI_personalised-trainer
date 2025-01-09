const MAX_LANGUAGES = 3;
const MAX_CERTIFICATIONS = 3;
const MAX_EDUCATION = 2;
const MAX_EXPERIENCE = 3;

function createNewField(type, index) {
  switch (type) {
    case "education":
      return `
                <div class="education-entry">
                    <input type="text" name="education[${index}].degree" placeholder="Degree" />
                    <input type="text" name="education[${index}].institution" placeholder="Institution" />
                    <input type="text" name="education[${index}].year" placeholder="Year" />
                    <button type="button" class="remove-btn" onclick="removeField(this, 'education')">Remove</button>
                </div>
            `;
    case "experience":
      return `
                <div class="experience-entry">
                    <input type="text" name="experience[${index}].role" placeholder="Role" />
                    <input type="text" name="experience[${index}].company" placeholder="Company" />
                    <input type="text" name="experience[${index}].duration" placeholder="Duration" />
                    <textarea name="experience[${index}].description" placeholder="Description (Max 25 words)"></textarea>
                    <button type="button" class="remove-btn" onclick="removeField(this, 'experience')">Remove</button>
                </div>
            `;
    case "language":
      return `
                <div class="language-entry">
                    <input type="text" name="languages[${index}].language" placeholder="Language" />
                    <select name="languages[${index}].proficiency">
                        <option value="Basic">Basic</option>
                        <option value="Intermediate">Intermediate</option>
                        <option value="Advanced">Advanced</option>
                        <option value="Native">Native</option>
                    </select>
                    <button type="button" class="remove-btn" onclick="removeField(this, 'language')">Remove</button>
                </div>
            `;
    case "certification":
      return `
                <div class="certification-entry">
                    <input type="text" name="certifications[${index}].title" placeholder="Certification Title" />
                    <input type="text" name="certifications[${index}].date" placeholder="Date (eg. Jan 2021)" />
                    <button type="button" class="remove-btn" onclick="removeField(this, 'certification')">Remove</button>
                </div>
            `;
    // Add other field types...
  }
}

function addField(type, maxEntries) {
  const container = document.getElementById(`${type}Container`);
  const entries = container.getElementsByClassName(`${type}-entry`);

  if (entries.length >= maxEntries) {
    alert(`You can only add up to ${maxEntries} ${type} entries.`);
    return;
  }

  const newEntry = createNewField(type, entries.length);
  container.insertAdjacentHTML("beforeend", newEntry);
}

function removeField(button, type) {
  button.closest(`.${type}-entry`).remove();
}

function validateForm() {
  const form = document.getElementById("resumeForm");
  const requiredFields = form.querySelectorAll("[required]");
  let isValid = true;

  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      field.classList.add("invalid");
      isValid = false;
    } else {
      field.classList.remove("invalid");
    }
  });

  // Validate word limits
  const professionalSummary = form.querySelector(
    '[name="professionalSummary"]'
  );
  if (professionalSummary.value.split(" ").length > 35) {
    alert("Professional Summary cannot exceed 35 words");
    isValid = false;
  }

  return isValid;
}

document.getElementById("resumeForm").onsubmit = function (e) {
  if (!validateForm()) {
    e.preventDefault();
  }
};
