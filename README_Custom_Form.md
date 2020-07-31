# MEMEX Project: Knowledge Graph - Custom Form Ingestion
The ingestion form has been created though the Google Form service, in particular by making use of Google Apps Script.

### Instructions
1. Visit the homepage of Google Apps Script (https://script.google.com/home)
	- Create an account if needed
	- Create a New Project / New Script
2. Write the following code to generate the form:
```
function createForm(){
	var form = FormApp.create('Ingestion_form');

	form.setTitle("Cultural Heritage insertion form")
	form.setDescription("This form is used to gather information about Cultural Heritage objects, in order to include them into the Knowledge Graph of Memex Project")

	form.addTextItem().setTitle("Title")
	.setHelpText("Insert the label of the Cultural Heritage object");
	form.addTextItem().setTitle("Description");
	form.addTextItem().setTitle('Author / Creator')
	.setHelpText("Insert the name of the creator/author of the object");

	cat_vector = []  // Insert the desired values for the category vector

	form.addListItem()
	.setTitle('Category')
	.setChoiceValues(cat_vector)
	.setRequired(true);
	form.addListItem()
	.setTitle('Additional category (Optional)')
	.setChoiceValues(cat_vector);
	form.addListItem()
	.setTitle('Additional category (Optional)')
	.setChoiceValues(cat_vector);
}
```
3. On top bar menu select the function createForm and click on the play button to execute the code
4. The form has been successfully created into your Google Drive