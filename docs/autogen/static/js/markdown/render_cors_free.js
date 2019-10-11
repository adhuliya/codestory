(function () {
  var reader = new stmd.DocParser();
  var writer = new stmd.HtmlRenderer();

  function display(markdown_content) {
    var parsed = reader.parse(markdown_content);
    var content = writer.renderBlock(parsed);
    document.getElementsByTagName('body')[0].innerHTML = content;
    
    /* try to extract h1 title and use as title for page
       if no h1, use name of file 
    */
    try {
      document.title = document.querySelector('h1').textContent
    } catch (e) {
      document.title = "Notes by LEG";
    }
  }

  display(this.fileContent);
})();

