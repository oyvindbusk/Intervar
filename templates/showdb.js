function polyform() {
  // send form
  $('input[id="submit"][value="Submit Polyphen"]').click();
 }
 //document ready function - happens on page load
$(function() {

  // fill comment if exists:
  $('#comment').val('{{ patient_comment[0] | replace("\r\n", "\\n") }}');
  $('#filtus_settings').html(' {{ patient_comment[1] | replace("\r\n", "\\n")    }}' );
  //fill the patient info modal with info on the specific patient in case you want to alter some values.
  $('#pID_Modal').on('shown.bs.modal', function (e) {
    $('#sex').val('{{ pID_patient.sex }}');
    $('#panel').val('{{ pID_patient.panel_name }}');
    $('#clinInfo').val('{{ pID_patient.clinInfo }}');
    $('#familyID').val('{{ pID_patient.familyID }}');
    $('#hsmFileUpload').val('{{ pID_patient.hsmFileUpload }}');
    $('#fragmentSizeUpload').val('{{ pID_patient.fragmentSizeUpload }}');
    });


  $('#filtus_settings').autosize();
  // hide ID col of table
  $('#variant_table td:nth-child(1),th:nth-child(1)').hide();
  $('th:first').show(); // This is hidden by mistake, so I have to show it.
  // hide signed and denovo col of table
  $('#variant_table td:nth-child(14),th:nth-child(14)').hide();
  $('#variant_table td:nth-child(16),th:nth-child(16)').hide();
  $('#variant_table td:nth-child(17),th:nth-child(17)').hide();
  // Hide variant table div if variant table is empty (e.g. contains the text: No Items):
  $("p:contains('No Items')").parent().hide();
  //change font in table:

  $('#variant_table').css("font-size", "11px");
  //tooltip on classes form selector
  $('#inhouse_class').tooltip({'trigger':'focus', 'title': 'Inhouse Class', 'placement': 'right'});
  $('#acmg_class').tooltip({'trigger':'focus', 'title': 'ACMG Class', 'placement': 'right'});

  // set a popover on combo input field containing info on howto:
  $('#combo').attr({
    "data-toggle":"popover",
    title:"How to use this input:",
    "data-content":"Simply copy the first 5 columns from Filtus and paste them into the field. Select zygosity and indicate denovo status, then press Submit to DB.",
    "data-trigger":"hover"
  });
  // set a popover on the get alamut button in the interp-modal
  $('#get_alamut').attr({
    "data-toggle":"popover",
    title:"What this does:",
    "data-content":"Click this button to append the alamut-info to the variant. If this does not work, use the input field below to compose your own request.",
    "data-trigger":"hover"
  });
  // Initialize all popovers and set size of popover:
  $('[data-toggle="popover"]').popover({
    container: 'body'
  });

 //Check if a ref & alt is letter as opposed to -. And also check if length == 1. This would mean missense.
 function isOneLetter(str) {
   return str.length === 1 && str.match(/[a-z]/i);
 }
 function isLetter(str) {
   return str.match(/[a-z]/i);
 }
 // Check if variant is:
 // missense
 // del
 // insertion
 // duplication -> get_alamut
 $('#get_alamut').click(function () {
   var assembly = "(GRCh37)";
   var alamut_request = "";
   // Get input
   if (isOneLetter(ref) && isOneLetter(alt)) {
     alamut_request = "chr" + chrom  + assembly + ":g." + start + ref + ">" + alt;
   } else if (isLetter(ref) && isLetter(alt) !== true) {
     alamut_request = "chr" + chrom + assembly + ":g." + start + "_" + stop + "del";
   } else if ( isLetter(ref) !== true && isLetter(alt)) {
     alamut_request = "chr" + chrom + assembly + ":g." + start + "_" + stop + "ins" + alt;
   }
   // get info from Alamut on click:
   $.getJSON("http://localhost:10000/show?request=" + alamut_request + "&synchronous=true", function(result){
     // Adds the original positions from the input, in case it differs from what is used by alamut
     result.ori_chr = chrom;
     result.ori_start = start;
     result.ori_stop = stop;
     result.ori_ref = ref;
     result.ori_alt = alt;
     console.log(JSON.stringify(result));
     $.ajax({
       type: "POST",
       contentType: "application/json; charset=utf-8",
       url: "/showdb/" + '{{ pID }}',
       data: JSON.stringify(result),
       success: function (data) {
         alert("Succesfully retrieved data from Alamut!");
       },
       dataType: "json"
     }).always(function() {location.reload(forceGet=true);console.log('Finito ajax POST to fLASK');});


          // Could the above be replaced by something like?:
     //$.getJSON('/showdb/' + '{{ pID }}', JSON.stringify(result), function(data) {alert("Succesfully retrieved data from Alamut!");} );
     //

   }).fail(function() {console.log('something went amiss with the GET');});

 });

//on click of: submitcDNARequest get value from: cDNARequest
$('#submitcDNARequest').click(function () {
  var alamut_request_cDNA = $('#cDNARequest').val();
  console.log(alamut_request_cDNA);
  // remove the last underscore in NM_2927_2 and replace with .
  // if string contains two underscores:
  // replace the last underscore with a period (.)
  //overwrite the original varible
  if ( (alamut_request_cDNA.match(/_/g) || []).length == 2 ) {
      var alamut_request_cDNA_clean =  alamut_request_cDNA.replace(/([^a-zA-Z])(_)/, "$1.");
      alamut_request_cDNA = alamut_request_cDNA_clean;
  }
  // alter from c.T1836C -> c.1836T>C
  // IF c. is followed by a char, not a number and > not present in string
  // Move the first character +> immediatly following the numbers
if ( alamut_request_cDNA.match(/:c\.[a-zA-Z]/) && !(alamut_request_cDNA.match(/>/)) ) {
  var req_pos = alamut_request_cDNA.match(/c\.[a-zA-Z]([0-9]*)/)[1];
  var req_ref = alamut_request_cDNA.match(/c\.([a-zA-Z])[0-9]/)[1];
  var req_alt = alamut_request_cDNA.match(/c\.[a-zA-Z][0-9]*([a-zA-Z])/)[1];
  var alamut_request_cDNA_correct = alamut_request_cDNA.replace(/c\.[a-zA-Z0-9]*/, 'c.' + req_pos + req_ref + '>' + req_alt);
  alamut_request_cDNA = alamut_request_cDNA_correct;
}

$.getJSON("http://localhost:10000/show?request=" + alamut_request_cDNA + "&synchronous=true", function(result){
  // Adds the original positions from the input, in case it differs from what is used by alamut
  result.ori_chr = chrom;
  result.ori_start = start;
  result.ori_stop = stop;
  result.ori_ref = ref;
  result.ori_alt = alt;
  $.ajax({
    type: "POST",
    contentType: "application/json; charset=utf-8",
    url: "/showdb/" + '{{ pID }}',
    data: JSON.stringify(result),
    success: function (data) {
      alert("Succesfully retrieved data from Alamut!");
    },
    dataType: "json"
  });
}).fail(function() {alert('test');});

});
//Then run request


// on click of polyphen, show entry form and submit button.
$('#ppt').click(function () {
if($('#pp').css('display') != 'none'){
  $('#polyphen').show();
  $('#pp').hide();
} else {
  $('#pp').show();
  $('#polyphen').hide();
}
});
// Refresh page on exit modal:
//$('#Interp_Modal').focusout(function () {location.reload()});
// making these variables global to the doc.ready function to be accessible in the scope of several functions.
var chrom;
var start;
var stop;
var ref;
var alt;
//get from variant table @ click:
$('#variant_table tr').click(function () {
var ID = $(this).closest("tr").find('td:eq(0)').text();
chrom = $(this).closest("tr").find('td:eq(1)').text();
start = $(this).closest("tr").find('td:eq(2)').text();
stop = $(this).closest("tr").find('td:eq(3)').text();
ref = $(this).closest("tr").find('td:eq(4)').text();
alt = $(this).closest("tr").find('td:eq(5)').text();
var zyg = $(this).closest("tr").find('td:eq(6)').text();
var comments = $(this).closest("tr").find('td:eq(12)').text();
var seenatmgm = $(this).closest("tr").find('td:eq(14)').text();
var denovostatus = $(this).closest("tr").find('td:eq(15)').text();
var denovoverbatim = '';
if (denovostatus == '0') {
  denovoverbatim = 'Not denovo';
} else if (denovostatus == '1') {
  denovoverbatim = 'Denovo';
} else {
  denovoverbatim = 'Undetermined';
}

var polyphen = $(this).closest("tr").find('td:eq(15)').text();
console.log(polyphen);
//fill hidden varid field for the alamut-field with variant ID:
$('#variant_id').val(String(chrom)+'|'+String(start)+'|'+String(stop)+'|'+String(ref)+'|'+String(alt));
$('#agene').text('');
$('#atrans').text('');
$('#agDNA').text('');
$('#aprot').text('');
$('#atype').text('');
$('#ahgmd').text('');
$('#adbsnp').text('');
$('#a1kg').text('');
$('#aESP').text('');
$('#aExac').text('');
$('aProtDom').text('');
//alamut variables:
$.getJSON($SCRIPT_ROOT + '/_return_alamut_for_variant', {
  id: parseInt(ID)
}, function(data) {
  $('#agene').text(data.gene);
  $('#atrans').text(data.transcript);
  $('#agDNA').text(data.gNomen);
  $('#acDNA').text(data.cNomen);
  $('#aprot').text(data.pNomen);
  $('#atype').text(data.codingEffect);
  // if hgmd gene ID is present, insert html link to HGMD:
  if (data.hgmdId) {
    // makes an anchor tag, sets the anchor text, creates the URL, connects the URL to the anchor, adds the anchor as a child to the dd-tag.
    var a = document.createElement('a');
    a.innerHTML = data.hgmdId;
    var hgmdvariantLink = "https://portal.biobase-international.com/hgmd/pro/mut.php?accession=" + data.hgmdId;
    a.setAttribute('href', hgmdvariantLink);
    $('#hgmdId').append(a);
  }
  $('#hgmdPhenotype').text(data.hgmdPhenotype);
  $('#hgmdSubCategory').text(data.hgmdSubCategory);
  $('#clinVarPhenotypes').text(data.clinVarPhenotypes);
  $('#adbsnp').text(data.rsId);
  $('#a1kg').text(data.rsMAF);
  $('#aESP').text(data.espAllMAF+ "(" + data.espAltAllCount + "/" + data.espRefAllCount + ")" );
  $('#aExac').text(data.exacAllFreq + "(" + data.exacAlleleCount + ")" );
  $('#aProtDom1').text(data.proteinDomain1);
  $('#aProtDom2').text(data.proteinDomain2);
  $('#aProtDom3').text(data.proteinDomain3);
  $('#Exon').text(data.exon);
  $('#alaclass').text(data.pathogenicityClass);
  $('#granthamDist').text(data.granthamDist);
  $('#comments').val(comments);
  $('#pub2varID').val(ID);
  $('#zygo').text(zyg);
  $('#mgmseen').text(seenatmgm);
  $('#denovostatus').text(denovoverbatim);
  $('#funcStud').text('Kommer!');
  $('#varLocation').text(data.varLocation);
  $('#localSpliceEffect').text(data.localSpliceEffect);
  $('#rsClinicalSignificance').text(data.rsClinicalSignificance);
  $('#exacNFEFreq').text(data.exacNFEFreq);
  $('#espEAMAF').text(data.espEAMAF + "(" + data.espAltEACount + ")" + data.espRefEACount);
  $('#clinVarClinSignifs').text(data.clinVarClinSignifs);
  $('#conservedOrthos').text(data.conservedOrthos);
  $('#AGVDclass').text(data.AGVGDclass);
  $('#SIFTPrediction').text(data.SIFTprediction);
  $('#TASTERprediction').text(data.TASTERprediction);
  $('pp').val(polyphen);
  // only show if present
  if (data.publications) {
      $('#pubs').show();
      $('#pubsTitle').show();
      $('#pubs').html(data.publications);
  }  else {
      $('#pubs').hide();
      $('#pubsTitle').hide();
  }
  // Set to 0 if empty:
  if (data.wtMaxEntScore) {
      $('#wtMaxEntScore').html(data.wtMaxEntScore);
  } else {
      $('#wtMaxEntScore').html(0);
  }
  if (data.varMaxEntScore) {
      $('#varMaxEntScore').html(data.varMaxEntScore);
  } else {
      $('#varMaxEntScore').html(0);
  }
  if (data.wtNNSScore) {
     $('#wtNNSScore').html(data.wtNNSScore);
  } else {
      $('#wtNNSScore').html(0);
  }
  if (data.varNNSScore) {
      $('#varNNSScore').html(data.varNNSScore);
  } else {
      $('#varNNSScore').html(0);
  }
  if (data.wtHSFScore) {
     $('#wtHSFScore').html(data.wtHSFScore);
  } else {
      $('#wtHSFScore').html(0);
  }if (data.varHSFScore) {
      $('#varHSFScore').html(data.varHSFScore);
  } else {
      $('#varHSFScore').html(0);
  }
  //find empty cols, and hide or make them grey
  $("dd:not(:empty)").prev().andSelf().css('opacity', '1.0');
  $("dd:empty").prev().andSelf().css('opacity', '0.5');

  //Fill Anchor tag of exac with link to exac variant.
  var exacLink = "http://exac.broadinstitute.org/variant/" + chrom + "-" + start + "-" + ref + "-" + alt;
  var hgmdGeneLink = "https://portal.biobase-international.com/hgmd/pro/gene.php?gene=" + data.gene;
  document.getElementById("exaclink").setAttribute("href", exacLink);
  document.getElementById("hgmdgenelink").setAttribute("href", hgmdGeneLink);
});
// Fill hidden form field with variant ID for the delete variant button:
$('#hidden_variant_ID').val(String(chrom)+'|'+String(start)+'|'+String(stop)+'|'+String(ref)+'|'+String(alt));
//$('.variant_info').html(chrom + " " + start + " " + stop);
$('#Interp_Modal').modal('show');
$('#varid').val(String(chrom)+'|'+String(start)+'|'+String(stop)+'|'+String(ref)+'|'+String(alt));

});
});
