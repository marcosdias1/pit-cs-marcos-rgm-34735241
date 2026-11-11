// preenche rua, bairro, cidade e estado quando a pessoa digita o CEP (cartão 20)
// usa o serviço gratuito ViaCEP (https://viacep.com.br)
// se der erro ou não achar o CEP, a pessoa preenche na mão (o formulário funciona do mesmo jeito)

// pega os campos da página (se a página não tem o campo de cep, não faz nada)
var campoCep = document.getElementById("cep");
var campoRua = document.getElementById("rua");
var campoNumero = document.getElementById("numero");
var campoBairro = document.getElementById("bairro");
var campoCidade = document.getElementById("cidade");
var campoUf = document.getElementById("uf");
var avisoCep = document.getElementById("cep-aviso");

// guarda o último cep que já foi buscado (pra não buscar o mesmo cep duas vezes)
var ultimoCepBuscado = "";


// função que busca o endereço do cep e preenche os campos
function buscarCep() {
    // deixa só os números
    var cep = campoCep.value.replace(/\D/g, "");

    // só busca quando tem os 8 números
    if (cep.length != 8) {
        return;
    }
    if (cep == ultimoCepBuscado) {
        return;
    }
    ultimoCepBuscado = cep;

    avisoCep.textContent = "Buscando o endereço...";

    fetch("https://viacep.com.br/ws/" + cep + "/json/")
        .then(function (resposta) {
            return resposta.json();
        })
        .then(function (dados) {
            // o viacep devolve erro: true quando não acha o cep
            if (dados.erro) {
                avisoCep.textContent = "CEP não encontrado. Preencha o endereço à mão.";
                return;
            }

            // CEP geral de cidade pequena não tem rua nem bairro, então só preenche o que veio
            if (dados.logradouro) {
                campoRua.value = dados.logradouro;
            }
            if (dados.bairro) {
                campoBairro.value = dados.bairro;
            }
            campoCidade.value = dados.localidade;
            campoUf.value = dados.uf;

            avisoCep.textContent = "Endereço encontrado. Confira e digite o número.";
            campoNumero.focus();
        })
        .catch(function (erro) {
            // console.log(erro);
            avisoCep.textContent = "Não foi possível buscar o CEP agora. Preencha o endereço à mão.";
        });
}


// só liga o javascript se a página tem todos os campos
if (campoCep != null && campoRua != null && campoNumero != null && campoBairro != null
        && campoCidade != null && campoUf != null && avisoCep != null) {

    campoCep.addEventListener("input", buscarCep);
    campoCep.addEventListener("blur", buscarCep);
}