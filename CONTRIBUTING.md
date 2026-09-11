# 🤝 Como Contribuir no Portfólio Dinâmico com Django

Este repositório não é apenas um site pessoal, mas um laboratório de boas práticas em **Django e Segurança Web**. Sua colaboração é muito bem-vinda para manter este material como uma referência técnica para a comunidade de desenvolvedores!

## 🚀 O que você pode aprimorar?

1.  **Novas Camadas de Segurança:** Implementar logs de tentativas de invasão ou integração com serviços de verificação de e-mail.
2.  **Performance Frontend:** Sugerir melhorias no `main.js` para otimização de renderização ou novos efeitos de UI.
3.  **Expansão de Testes:** Aumentar a cobertura de testes para os modelos de dados e sinais do Django.
4.  **Documentação:** Melhorar os comentários técnicos ou traduzir a documentação para outros idiomas.

## 🛠️ Como enviar sua sugestão:

1.  Faça o **Fork** do projeto.
2.  Crie uma branch para sua modificação: `git checkout -b feature/melhoria-tecnica`.
3.  Realize seus commits seguindo o padrão **Conventional Commits** (ex: `feat:`, `fix:`, `security:`).
4. Envie suas alterações para o seu fork: `git push origin feature/nome-da-melhoria`.
5.  Rode o portão de qualidade completo (ver [README → Qualidade e testes](README.md#qualidade-e-testes)) e garanta que está tudo verde.
6.  Abra um **Pull Request** detalhando tecnicamente o que foi alterado e o impacto da mudança.

## 📜 Diretrizes de Qualidade:
- **PEP 8:** O código Python deve seguir rigorosamente os padrões de estilo (aplicado automaticamente por `ruff`/`black` — ver README).
- **Segurança:** Nunca envie código que exponha credenciais ou desative proteções de `SSL/CSP` sem justificativa técnica.
- **Nomenclatura:** Mantenha a coerência semântica já estabelecida no projeto.
- **Testes:** toda mudança de comportamento (nova regra, correção de bug) vem acompanhada de um teste que a cubra — sem isso, o PR não é aceito.

---
Atenciosamente,  
**Ryan Morais**