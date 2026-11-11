// faz o filtro por categoria e a busca funcionarem SEM recarregar a página (cartão 02)


// pega os elementos da página
var formBusca = document.getElementById("form-busca");
var campoBusca = document.getElementById("campo-busca");
var campoCategoria = document.getElementById("campo-categoria");
var grade = document.getElementById("grade");
var avisoVazio = document.getElementById("aviso-vazio");
var erroJs = document.getElementById("erro-js");
var chips = document.querySelectorAll(".chip");

// guarda a categoria escolhida (vem do html, vazio quer dizer "Todos")
var categoriaAtual = campoCategoria.value;

// esse número serve pra ignorar respostas antigas (se a pessoa digita rápido, a resposta velha pode chegar depois da nova)
var numeroDoPedido = 0;

// guarda o tempo de espera da busca
var temporizador = null;


// função que desenha os cupcakes na grade
function desenharCupcakes(lista) {
    // limpa a grade
    grade.innerHTML = "";

    for (var i = 0; i < lista.length; i++) {
        var c = lista[i];

        // cria o card (tem que ficar igualzinho ao do vitrine.html)
        var card = document.createElement("div");
        card.className = "card";

        var foto = document.createElement("div");
        foto.className = "foto";
        foto.textContent = "🧁";

        var nome = document.createElement("div");
        nome.className = "nome";
        var link = document.createElement("a");
        link.href = "/cupcake/" + c.id;
        // textContent é mais seguro que innerHTML (não deixa rodar html que vier do banco)
        link.textContent = c.nome;
        nome.appendChild(link);

        var categoria = document.createElement("div");
        categoria.className = "categoria";
        categoria.textContent = c.categorias;

        var preco = document.createElement("div");
        preco.className = "preco";
        preco.textContent = c.preco;

        card.appendChild(foto);
        card.appendChild(nome);
        card.appendChild(categoria);
        card.appendChild(preco);
        grade.appendChild(card);
    }

    // se não veio nenhum, mostra o aviso
    if (lista.length == 0) {
        if (categoriaAtual != "" || campoBusca.value.trim() != "") {
            avisoVazio.textContent = "Nenhum cupcake encontrado. Tente outra busca ou outra categoria.";
        } else {
            avisoVazio.textContent = "Nenhum cupcake disponível no momento.";
        }
        avisoVazio.hidden = false;
    } else {
        avisoVazio.hidden = true;
    }
}


// função que mostra uma mensagem de erro em cima da lista
function mostrarErro(texto) {
    erroJs.textContent = texto;
    erroJs.hidden = false;
}


// função que guarda o filtro na url (assim, se apertar F5, o filtro continua)
function guardarNaUrl() {
    var endereco = "/?categoria=" + encodeURIComponent(categoriaAtual) + "&busca=" + encodeURIComponent(campoBusca.value);
    history.replaceState(null, "", endereco);
}


// função que pede os cupcakes pro servidor e desenha na tela
function atualizar() {
    numeroDoPedido = numeroDoPedido + 1;
    var meuNumero = numeroDoPedido;

    var endereco = "/api/cupcakes?categoria=" + encodeURIComponent(categoriaAtual) + "&busca=" + encodeURIComponent(campoBusca.value);

    fetch(endereco)
        .then(function (resposta) {
            // 401 quer dizer que a sessão acabou, então volta pro login
            if (resposta.status == 401) {
                window.location.href = "/login";
                return { sessaoAcabou: true };
            }
            return resposta.json();
        })
        .then(function (dados) {
            if (dados.sessaoAcabou) {
                return;
            }
            // se chegou uma resposta velha, ignora
            if (meuNumero != numeroDoPedido) {
                return;
            }
            // o servidor avisou que deu erro
            if (dados.erro) {
                mostrarErro(dados.erro);
                return;
            }
            erroJs.hidden = true;
            desenharCupcakes(dados.cupcakes);
            guardarNaUrl();
        })
        .catch(function (erro) {
            // console.log(erro);
            if (meuNumero == numeroDoPedido) {
                mostrarErro("Não foi possível atualizar a lista. Tente de novo em alguns minutos.");
            }
        });
}

// quando clica num botão de categoria
for (var i = 0; i < chips.length; i++) {
    chips[i].addEventListener("click", function (evento) {
        // não deixa o link recarregar a página
        evento.preventDefault();

        categoriaAtual = this.getAttribute("data-id");
        campoCategoria.value = categoriaAtual;

        // desmarca todos e marca só o que foi clicado
        for (var j = 0; j < chips.length; j++) {
            chips[j].classList.remove("chip-ativo");
            chips[j].removeAttribute("aria-current");
        }
        this.classList.add("chip-ativo");
        this.setAttribute("aria-current", "true");

        atualizar();
    });
}

// quando digita na busca (espera 300 milissegundos depois da última tecla)
campoBusca.addEventListener("input", function () {
    clearTimeout(temporizador);
    temporizador = setTimeout(atualizar, 300);
});

// o enter no campo de busca não pode recarregar a página
formBusca.addEventListener("submit", function (evento) {
    evento.preventDefault();
    clearTimeout(temporizador);
    atualizar();
});