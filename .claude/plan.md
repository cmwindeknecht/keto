## MVP Plan
1. The ability to lookup single ingredients and the UI will show the nutrients.  
* It will list out if something is good for keto or not (I'll make up the logic here).  
* It will allow you to switch between grams, ounces, fluid ounces, etc and input the amount 
2. The ability to lookup products to see how keto they are.
* Provide a list of each ingredient of the product that states why it is / isn't keto safe.
3. The abilty to create a recipe
* Summarizes the keto related data (number of servings, net carbs per serving, electroylytes, etc) as you make it (so you don't make a whole recipe and find out its too high in carbs or whatever)
4. The ability to look at recipes that others have created.  
* Rated 0/100 for how keto something is based on quality of ingredients and "ketoness" of a serving.  (All ingredients/recipes should have this rating --- I'll make up the rules).

## MVP Considerations
1. Cache USDA requests for 30 days for ingredients / products / etc
2. Rules should use a rules engine like camunda?

## Future Features
1. User accounts to own recipes
2. Ability to add data not found in the USDA (primary use case would be random keto goods that people buy but are not found, I assume this is somewhat common from my experience using calorie tracking type apps)