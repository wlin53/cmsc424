const dropdown = document.getElementById('dropdown');

const descriptions = {
  eyq: 'Data for a given election year (1789-2016)',
  pcq: 'Data for a given candidate or president',
  rncq: 'Presidents re-elected after losing one or more elections in between',
  scq: 'Candidates who ran on different parties in different elections',
  phq: 'Yearly and cumulative data for a given party',
  ceq: 'Closest elections by popular vote',
  llvq: 'Elections with the largest difference in popular vote',
  mppq: 'Presidents with the highest percent of popular vote in an election',
  lrpq: 'Lowest ranking presidents according to the Rasmussen poll'
};

// creates extra input boxes based on query
function updateExtraInput(value) {

  const extra = document.getElementById('extra');

  extra.innerHTML = '';
  extra.appendChild(document.createTextNode(descriptions[value]));

  if (value === 'eyq')
    extra.appendChild(createInput('Enter Year:'))

  else if (value === 'pcq')
    extra.appendChild(createInput('Enter Name:'))

  else if (value === 'phq')
    extra.appendChild(createInput('Enter Party:'))
}

updateExtraInput(dropdown.value);

function createInput(label) {

  const wrapper = document.createElement('div');
  const input = document.createElement('input');
  input.id = 'extra-input';
  input.type = 'text';
  wrapper.appendChild(document.createTextNode(label));
  wrapper.appendChild(input);

  return wrapper;
}

dropdown.addEventListener('change', function() {
  updateExtraInput(dropdown.value);
});

const lookupUrl = {
  eyq:  '/election?year=',
  pcq:  '/president?name=',
  rncq: '/re-elected',
  scq:  '/swing',
  phq:  '/party?party=',
  ceq:  '/closest',
  llvq: '/landslide',
  mppq: '/most-popular',
  lrpq: '/lowest-ranking'
};

document.getElementById('button').addEventListener('click', function() {

  const value = dropdown.value;
  const extraInput = document.getElementById('extra-input');
  var url = lookupUrl[value]
  if (extraInput) {
    url = url.concat(extraInput.value);
  }
  const req = new XMLHttpRequest();
  req.addEventListener("load", function() {

    const data = JSON.parse(this.responseText);
    document.getElementById('results').innerHTML = '';
    if (value === 'phq') {

      createTable({
        columns: data.yearly_columns,
        data: data.yearly_data
      });

      createTable({
        columns: data.stats_columns,
        data: data.stats_data
      });
    }
    else {
      createTable(data);
    }
  });
  req.open("GET", url);
  req.send();
});

function createTable(data) {

  const table = document.createElement('table');

  // create the headers
  const headers = document.createElement('tr');
  data.columns.forEach(function(header) {

    const th = document.createElement('th');
    th.appendChild(document.createTextNode(header));
    headers.appendChild(th);
  });

  table.appendChild(headers);

  data.data.forEach(function(row) {

    const tr = document.createElement('tr');

    row.forEach(function(cell) {
      const td = document.createElement('td');
      td.innerText = cell;
      tr.appendChild(td);
    })

    table.appendChild(tr);
  });

  document.getElementById('results').appendChild(table);
}
