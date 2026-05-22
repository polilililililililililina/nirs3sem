def reset_password_template(reset_link: str):

    return f"""
    <html>
      <body style="
        font-family: Arial;
        padding: 20px;
      ">

        <h2>Восстановление пароля</h2>

        <p>
          Для сброса пароля нажмите кнопку:
        </p>

        <a
          href="{reset_link}"
          style="
            display: inline-block;
            padding: 12px 20px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 8px;
          "
        >
          Сбросить пароль
        </a>

        <p style="margin-top:20px;">
          Если это были не вы —
          проигнорируйте письмо.
        </p>

      </body>
    </html>
    """