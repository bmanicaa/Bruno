/**
 * seed_gramatica.js — Gera os TSVs do deck de GRAMÁTICA do Anki.
 *
 * MOTIVO: até aqui, só o vocabulário entrava no Anki. As 84 estruturas
 * gramaticais eram revistas apenas nas aulas de consolidação, cujos `scope`
 * nunca revisitam um bloco anterior — a gramática da Aula 2 só reaparecia na
 * Aula 32, um intervalo de 27 semanas. Este deck fecha esse buraco.
 *
 * Formato do card: recuperação ATIVA por produção — a frente traz uma frase
 * com lacuna mais a função comunicativa; o verso traz a forma e o porquê.
 *
 * Uso: node scripts/seed_gramatica.js [--check]
 */

const fs = require('fs');
const path = require('path');

const r = (kanji, kana) => `<ruby>${kanji}<rt>${kana}</rt></ruby>`;

// Slug de tag por ponto gramatical, para permitir estudo filtrado por estrutura.
const CARDS = [
    // ── AULA 1 ────────────────────────────────────────────────
    { aula: 1, g: 'desu', frase: `${r('私','わたし')}は${r('学生','がくせい')} ___ 。`, resp: 'です',
      est: 'N + です', exp: 'Cópula polida "ser/estar". Liga-se direto ao substantivo. Versão casual: だ.' },
    { aula: 1, g: 'desu', frase: `${r('母','はは')}は${r('医者','いしゃ')} ___ 。(registro polido)`, resp: 'です',
      est: 'N + です', exp: 'です é neutro-polido e serve para qualquer pessoa gramatical — não conjuga por pessoa como em português.' },
    { aula: 1, g: 'wa-topico', frase: `${r('私','わたし')} ___ ${r('留学生','りゅうがくせい')}です。`, resp: 'は',
      est: 'N + は', exp: 'Marca o TÓPICO ("quanto a mim, ..."). Escreve-se は mas pronuncia-se "wa". Define do que a frase trata, não quem pratica a ação.' },
    { aula: 1, g: 'wa-topico', frase: `${r('今日','きょう')} ___ ${r('漢字','かんじ')}の${r('言葉','ことば')}です。`, resp: 'は',
      est: 'N + は', exp: 'は pode marcar tempo como tópico: "quanto a hoje...". Contraste com が (Aula 3), que introduz informação nova.' },
    { aula: 1, g: 'ka-pergunta', frase: `あなたは${r('先生','せんせい')}です ___ 。`, resp: 'か',
      est: 'Frase + か', exp: 'Partícula final que transforma a afirmação em pergunta sim/não. Em japonês não é preciso inverter a ordem das palavras.' },
    { aula: 1, g: 'ka-pergunta', frase: `${r('外国人','がいこくじん')}です ___ 。(transformar em pergunta)`, resp: 'か',
      est: 'Frase + か', exp: 'Com か, o ponto de interrogação é opcional — a partícula já marca a pergunta.' },

    // ── AULA 2 ────────────────────────────────────────────────
    { aula: 2, g: 'janai', frase: `${r('私','わたし')}は${r('医者','いしゃ')} ___ です。(negar identidade)`, resp: 'じゃない',
      est: 'N + じゃない (です)', exp: 'Negativa da cópula. じゃない é casual; ではありません é formal. じゃないです é o meio-termo polido do dia a dia.' },
    { aula: 2, g: 'janai', frase: `${r('兄','あに')}は${r('学生','がくせい')} ___ 。(negar, casual)`, resp: 'じゃない',
      est: 'N + じゃない', exp: 'Sem です fica casual. じゃない é a contração falada de ではない.' },
    { aula: 2, g: 'no-posse', frase: `${r('私','わたし')} ___ ${r('本','ほん')}です。`, resp: 'の',
      est: 'N1 + の + N2', exp: `Marca posse ou atribuição: N1 é o possuidor, N2 o possuído. Ordem inversa à do português ("o livro de mim" → ${r('私','わたし')}の${r('本','ほん')}).` },
    { aula: 2, g: 'no-posse', frase: `${r('友達','ともだち')} ___ ${r('お母さん','おかあさん')}は${r('先生','せんせい')}です。`, resp: 'の',
      est: 'N1 + の + N2', exp: `の encadeia: ${r('友達','ともだち')}の${r('お母さん','おかあさん')} = "a mãe do amigo". Pode empilhar: ${r('私','わたし')}の${r('友達','ともだち')}の${r('お母さん','おかあさん')}.` },
    { aula: 2, g: 'mo', frase: `${r('私','わたし')} ___ ${r('留学生','りゅうがくせい')}です。(indicar adição)`, resp: 'も',
      est: 'N + も', exp: `"Também". SUBSTITUI は/が — nunca diga ${r('私','わたし')}はも. Com verbo negativo passa a significar "tampouco".` },
    { aula: 2, g: 'mo', frase: `${r('弟','おとうと')} ___ ${r('生徒','せいと')}です。(ele igualmente)`, resp: 'も',
      est: 'N + も', exp: 'Erro clássico de lusófono: manter は junto de も. も ocupa o lugar da partícula de tópico.' },
    { aula: 2, g: 'o-go-polidez', frase: `あなたの ___ は${r('医者','いしゃ')}です。(irmão mais velho DE OUTRA pessoa)`, resp: r('お兄さん','おにいさん'),
      est: `お + ${r('和語','わご')}`, exp: `Família alheia leva prefixo honorífico: ${r('お兄さん','おにいさん')}. Para a própria família usa-se a forma simples ${r('兄','あに')}. Confundir as duas soa arrogante ou distante.` },
    { aula: 2, g: 'o-go-polidez', frase: `${r('私','わたし')}の ___ は${r('会社','かいしゃ')}の${r('人','ひと')}です。(meu próprio pai)`, resp: r('父','ちち'),
      est: `${r('和語','わご')} sem prefixo`, exp: `Ao falar da PRÓPRIA família, use a forma sem honorífico: ${r('父','ちち')} / ${r('母','はは')} / ${r('兄','あに')} / ${r('姉','あね')}. Já ${r('お父さん','おとうさん')} e ${r('お母さん','おかあさん')} referem-se à família do interlocutor.` },

    // ── AULA 3 ────────────────────────────────────────────────
    { aula: 3, g: 'ga-sujeito', frase: `A: ${r('家族','かぞく')}は${r('医者','いしゃ')}ですか。B: ${r('父','ちち')} ___ ${r('医者','いしゃ')}です。`, resp: 'が',
      est: 'N + が', exp: 'が identifica QUEM, entre alternativas — é a informação nova que responde à pergunta. は apenas retomaria o tópico já conhecido.' },
    { aula: 3, g: 'ga-sujeito', frase: `${r('女の子','おんなのこ')} ___ ${r('生徒','せいと')}です。(apontar quem, informação nova)`, resp: 'が',
      est: 'N + が', exp: 'Regra prática: は = o que já está em pauta; が = o que entra em cena agora ou responde a "quem/qual".' },
    { aula: 3, g: 'ga-mas', frase: `${r('兄','あに')}は${r('学生','がくせい')}です ___ 、${r('私','わたし')}は${r('医者','いしゃ')}です。(contraste)`, resp: 'が',
      est: 'Oração + が + Oração', exp: 'O MESMO が também liga duas orações com sentido de "mas". Distinga pela posição: depois de です/ます é conjunção, depois de substantivo é sujeito.' },
    // とても (grammar #77) foi MOVIDO para a Aula 4, onde estreiam os adjetivos
    // que ele modifica. O card correspondente entra em N5_G4_Gramatica.tsv
    // quando a Aula 4 for gerada — deliberadamente ausente aqui.
    { aula: 3, g: 'ka-ka', frase: `${r('先生','せんせい')} ___ ${r('医者','いしゃ')} ___ ですか。(duas alternativas)`, resp: 'か / か',
      est: 'A か B か', exp: 'Apresenta alternativas: "A ou B?". Cada item recebe seu próprio か; o か final da frase faz a pergunta.' },
    { aula: 3, g: 'ka-ka', frase: `${r('本','ほん')}は${r('一つ','ひとつ')} ___ ${r('二つ','ふたつ')}ですか。`, resp: 'か',
      est: 'A か B か', exp: 'Na fala, o か depois do segundo item costuma cair, restando só o か da pergunta.' },
];

function faseDaAula(n) { return n <= 5 ? 1 : n <= 9 ? 2 : n <= 13 ? 3 : n <= 18 ? 4 : n <= 26 ? 5 : 6; }

function main() {
    const check = process.argv.includes('--check');
    const porAula = {};
    for (const c of CARDS) (porAula[c.aula] ||= []).push(c);

    const cabecalho = [
        '#separator:tab',
        '#html:true',
        '#notetype:N5 Gramática',
        '#deck:Japonês::N5::Gramática',
        '#tags column:5',
        '#columns:Frase\tResposta\tEstrutura\tExplicacao\tTags',
    ].join('\n');

    let total = 0;
    for (const [aula, cards] of Object.entries(porAula)) {
        const linhas = cards.map((c) => {
            const tags = `aula::${String(c.aula).padStart(2, '0')} fase::${faseDaAula(c.aula)} tipo::gramatica gramatica::${c.g}`;
            return [c.frase, c.resp, c.est, c.exp, tags].join('\t');
        });
        const destino = path.join(__dirname, `../Anki/N5_G${aula}_Gramatica.tsv`);
        const conteudo = cabecalho + '\n' + linhas.join('\n') + '\n';
        if (!check) fs.writeFileSync(destino, conteudo, 'utf8');
        console.log(`N5_G${aula}_Gramatica.tsv: ${linhas.length} cards`);
        total += linhas.length;
    }
    console.log(`\n${check ? '[--check] ' : ''}Total: ${total} cards de gramática.`);
}

if (require.main === module) main();
module.exports = { CARDS };
