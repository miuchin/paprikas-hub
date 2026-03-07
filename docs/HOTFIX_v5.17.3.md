# HOTFIX vv5.17.3

Ispravljen front-end crash:

- `Uncaught SyntaxError: Unexpected end of input`
- uzrok: unutrašnji `</script>` u Prompt Helper HTML template string-u
- rešenje: zatvoren kao `<\/script>` da ne prekine glavni `<script>` u `index.html`

Dodatno:
- poravnate glavne verzione oznake u headeru/home delu na `v5.17.3`
- zadržan server indentation hotfix iz prethodne verzije
