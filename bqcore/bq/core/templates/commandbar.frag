<html xmlns="http://www.w3.org/1999/xhtml"   
    xmlns:xi="http://www.w3.org/2001/XInclude"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:py="http://genshi.edgewall.org/"
    py:strip=""
    >

<div class="commandbar" id="searchbox" >
  <div>

    <input py:if="value_of('search_text', default=True)" type="text" size="50" id="query" value="${value_of('query', '')}"  />      
    <input py:if="not value_of('search_text', default=True)" type="hidden" id="query" value="${value_of('query', '')}" />
    <button class="cmdBarButton" id='searchbtn' value="Search" title="search for your text query (wildcard is *)" >Search</button>
  
<button py:if="value_of('search_text', default=True)" class="cmdBarButton" id='downloadbtn' value="Download" title="Download your text query (wildcard is *)" onclick="downloadImages()">Download</button>
    <input py:if="value_of('search_public', default=True)" type='checkbox' id='wpublic' checked='${tg.checker( value_of("wpublic", default=False) )}' />

	<input py:if="not value_of('search_public', default=True)" type='hidden' id='wpublic' checked='${tg.checker( value_of("wpublic", default=False) )}' value='${tg.checker( value_of("wpublic", default=False) )}' />			
      <span py:if="value_of('search_public', default=True)">Include public images</span>


    <button class="cmdBarButton" py:if="value_of('search', default=False)" value="advanced search" title="Search using tags and other features."     onclick="showOrganizer()">Organize</button>

    <button class="cmdBarButton" py:if="value_of('search', default=False)" value="datasets" title="work with groups of images" onclick="showDatasetBrowser()">Datasets</button>

    <button py:if="value_of('analysis', default=False)" class="cmdBarButton" value="analysis" title="perform a range of analyses on this image" onclick="showAnalysis('${resource}', '${bq.identity.get_user_id()}')">Analysis</button>

    <button py:if="value_of('visualization_button', default=False)" class="cmdBarButton" value="visualization" title="view interactive graphs of analysis results (when available)" onclick="loadVisualizer('${resource}')">visualize results</button>

    <button py:if="value_of('upload_button', default=True)" class="cmdBarButton" value="upload"  title="upload your own images for analysis" onclick="javascript:window.location.href='/bisquik/upload_progress';">Upload</button>

  <script>
//     jQuery(document).ready(function () {
    Ext.onReady(function () {
         _SB = new SearchBox('commandbar', 'query', 'wpublic', 'searchbtn'); 
    });

function downloadImages() {
    var query=document.getElementById("query").value;
    var view="short";
    var wpublicVal=document.getElementById("wpublic").value;
    if(query == "") {
        alert("Please enter a search string");
        return;
    }

    if(wpublicVal == "on") {
        wpublic="true";
    } else {
        wpublic="false";
    }
    var offset=0;
    var action="/export/checkDownloadTar?tag_query="+query+"&amp;view="+view+"&amp;wpublic="+wpublic+"&amp;offset="+offset;
    document.location.href=action;
}
</script>
  </div>

</div>

</html>
