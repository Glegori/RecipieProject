db.recipies.find({"Preparation.Servings":{$exists: true}}).forEach( function (x) {
    x.Preparation.Servings = new NumberInt(x.Preparation.Servings);
    db.recipies.save(x)
    })