const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 4200;

app.use(express.static(__dirname + '/dist'));
app.get('/*', function(req, res) {
  res.sendFile(path.join(__dirname + '/dist/index.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});